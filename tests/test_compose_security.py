import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit
COMPOSE_PATH = Path(__file__).resolve().parent.parent / "docker-compose.yml"


@pytest.fixture(scope="module")
def services():
    return yaml.safe_load(COMPOSE_PATH.read_text(encoding="utf-8"))["services"]


@pytest.mark.parametrize("service", ["web", "web-worker"])
@pytest.mark.parametrize("key", ["SECRET_KEY", "JWT_SECRET_KEY"])
def test_compose_requires_explicit_signing_keys(services, service, key):
    value = services[service]["environment"][key]
    assert value.startswith(f"${{{key}:?")
    assert value.endswith("}")


@pytest.mark.parametrize("name,port", [("spider", 8090), ("nlp", 8091)])
def test_auxiliary_service_is_internal_and_receives_the_web_token(services, name, port):
    service = services[f"{name}-api"]
    web_env = services["web"]["environment"]
    key = f"{name.upper()}_SERVICE_TOKEN"

    assert not service.get("ports")
    assert f"http://localhost:{port}/health" in " ".join(service["healthcheck"]["test"])
    assert web_env[f"{name.upper()}_SERVICE_BASE_URL"] == f"http://{name}-api:{port}"
    assert service["environment"][key] == web_env[key]
    assert web_env[key].startswith(f"${{{key}:?")


@pytest.mark.parametrize("service", ["web", "web-worker"])
def test_compose_does_not_grant_any_admin_by_default(services, service):
    assert services[service]["environment"]["ADMIN_USERS"] == "${ADMIN_USERS:-}"


def test_web_worker_validates_configuration_before_starting_celery(services):
    shell, options, script = services["web-worker"]["command"]
    assert (shell, options) == ("sh", "-ec")
    assert script.index("Config.validate()") < script.index("exec celery")


def test_compose_binding_and_database_credentials(services):
    mysql = services["mysql"]
    redis = services["redis"]
    assert not mysql.get("ports")
    assert not redis.get("ports")
    assert services["web"]["ports"] == ["127.0.0.1:5000:5000"]

    for key in ("MYSQL_ROOT_PASSWORD", "MYSQL_PASSWORD"):
        assert mysql["environment"][key].startswith("${" + key + ":?")
    assert mysql["environment"]["MYSQL_ROOT_HOST"] == "localhost"
    for name in ("web", "web-worker", "spider-api", "spider-worker"):
        env = services[name]["environment"]
        assert env["DB_USER"] == mysql["environment"]["MYSQL_USER"]
        assert env["DB_PASSWORD"] == mysql["environment"]["MYSQL_PASSWORD"]
        assert "MYSQL_ROOT_PASSWORD" not in str(env)

    for service in services.values():
        env = service.get("environment", {})
        if "REDIS_PASSWORD" in env:
            assert env["REDIS_PASSWORD"] == redis["environment"]["REDIS_PASSWORD"]
    assert redis["environment"]["REDIS_PASSWORD"].startswith("${REDIS_PASSWORD:?")
    assert "--requirepass" in redis["command"][2]
    assert "REDISCLI_AUTH" in redis["healthcheck"]["test"][1]


def test_mysql_initialization_does_not_seed_accounts(services):
    volumes = services["mysql"]["volumes"]
    init_mount = next(item for item in volumes if "/docker-entrypoint-initdb.d/" in item)
    source = init_mount.split(":", 1)[0]
    sql = (COMPOSE_PATH.parent / source).read_text(encoding="utf-8").upper()
    assert "CREATE TABLE `USER`" in sql
    assert "INSERT INTO `USER`" not in sql
    assert "DROP DATABASE" not in sql
    assert services["web"]["environment"]["AUTO_CREATE_DEMO_ADMIN"] == "False"


@pytest.mark.parametrize(
    ("service", "env", "valid"),
    [
        ("mysql", {"MYSQL_ROOT_PASSWORD": "", "MYSQL_PASSWORD": "b" * 64}, False),
        ("mysql", {"MYSQL_ROOT_PASSWORD": "root", "MYSQL_PASSWORD": "b" * 64}, False),
        ("mysql", {"MYSQL_ROOT_PASSWORD": "a" * 64, "MYSQL_PASSWORD": "a" * 64}, False),
        ("mysql", {"MYSQL_ROOT_PASSWORD": "a" * 64, "MYSQL_PASSWORD": "b" * 64}, True),
        ("redis", {"REDIS_PASSWORD": ""}, False),
        ("redis", {"REDIS_PASSWORD": "password"}, False),
        ("redis", {"REDIS_PASSWORD": "c" * 64}, True),
    ],
)
def test_database_and_redis_preflight(services, service, env, valid):
    shell = shutil.which("sh")
    if not shell:
        pytest.skip("Compose Linux entrypoint requires a POSIX shell")
    spec = services[service]
    command = spec["entrypoint"] if service == "mysql" else spec["command"]
    # Replace the container process with a no-op, exercising the actual preflight shell.
    script = command[2].split("exec docker-entrypoint.sh", 1)[0].replace("$$", "$")
    result = subprocess.run(
        [shell, "-ec", script],
        env={**os.environ, **env},
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert (result.returncode == 0) is valid
    if not valid:
        assert "PASSWORD" in result.stderr


def test_docker_compose_resolves_required_configuration(tmp_path):
    docker = shutil.which("docker")
    if not docker or subprocess.run(
        [docker, "compose", "version"], capture_output=True, timeout=15
    ).returncode:
        pytest.skip("Docker Compose CLI is unavailable")

    env_file = tmp_path / "empty.env"
    env_file.touch()
    command = [docker, "compose", "--env-file", str(env_file), "-f", str(COMPOSE_PATH), "config", "--quiet"]
    required = (
        "SECRET_KEY",
        "JWT_SECRET_KEY",
        "MYSQL_ROOT_PASSWORD",
        "MYSQL_PASSWORD",
        "REDIS_PASSWORD",
        "SPIDER_SERVICE_TOKEN",
        "NLP_SERVICE_TOKEN",
    )
    env = {**os.environ, **{key: f"{i:064x}" for i, key in enumerate(required, 1)}}
    result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr

    for key in required:
        result = subprocess.run(
            command, env={**env, key: ""}, capture_output=True, text=True, timeout=15
        )
        assert result.returncode != 0
        assert key in result.stderr
