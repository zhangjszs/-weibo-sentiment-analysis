from typing import Any, Dict, Optional

from models.user import User

from .base_repository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(User)

    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        user = self.session.query(User).filter_by(username=username).first()
        if user:
            return self._user_to_dict(user)
        return None

    def find_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        user = self.session.query(User).filter_by(id=user_id).first()
        if user:
            return self._user_to_dict(user)
        return None

    def create(self, username: str, password_hash: str, create_time: str) -> None:
        user = User(username=username, password=password_hash, create_time=create_time)
        self.save(user)

    def update_profile(self, user_id: int, **kwargs) -> bool:
        """Update user profile fields (nickname, email, bio, avatar_color)."""
        allowed_fields = {"nickname", "email", "bio", "avatar_color"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False
        try:
            self.session.query(User).filter_by(id=user_id).update(updates)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            return False

    def update_password(self, user_id: int, new_password_hash: str) -> bool:
        """Update user password."""
        try:
            self.session.query(User).filter_by(id=user_id).update(
                {"password": new_password_hash}
            )
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            return False

    @staticmethod
    def _user_to_dict(user: User) -> Dict[str, Any]:
        return {
            "id": user.id,
            "username": user.username,
            "password": user.password,
            "create_time": user.create_time,
            "nickname": user.nickname,
            "email": user.email,
            "bio": user.bio,
            "avatar_color": user.avatar_color,
        }
