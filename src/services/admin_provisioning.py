"""Create a configured administrator through an operator-only entry point."""

from sqlalchemy.exc import IntegrityError

from config.settings import Config
from models.user import User
from utils.datetime_utils import utcnow_naive
from utils.input_validator import validate_username
from utils.password_hasher import hash_password


def validate_admin_credentials(username: str, password: str) -> None:
    if username != username.strip() or not validate_username(username)["valid"]:
        raise ValueError("管理员用户名格式无效")
    if (
        not 15 <= len(password) <= 32
        or len(password.encode("utf-8")) > 72
        or password != password.strip()
    ):
        raise ValueError("请输入 15 到 32 字符的随机密码（最多 72 字节）")


def create_admin_account(username: str, password: str) -> bool:
    """Create an allowlisted account once, leaving existing identities untouched."""
    from database import db_session

    validate_admin_credentials(username, password)
    if username not in Config.ADMIN_USERS:
        raise ValueError("管理员用户名必须与 ADMIN_USERS 中的一项完全匹配")
    if db_session.query(User.id).filter_by(username=username).first() is not None:
        return False

    db_session.add(
        User(username=username, password=hash_password(password), create_time=utcnow_naive())
    )
    try:
        db_session.commit()
    except IntegrityError:
        db_session.rollback()
        return False
    return True
