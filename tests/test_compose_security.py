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
