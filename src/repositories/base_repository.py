from typing import Any, List, Optional

from sqlalchemy.exc import SQLAlchemyError

from database import db_session


class BaseRepository:
    """
    Base Repository class using SQLAlchemy.
    """

    def __init__(self, model):
        self.model = model
        self.session = db_session

    def find_all(self, limit: int = 100, offset: int = 0) -> List[Any]:
        return self.session.query(self.model).limit(limit).offset(offset).all()

    def find_by_id(self, id: Any) -> Optional[Any]:
        return self.session.query(self.model).get(id)

    def count(self) -> int:
        return self.session.query(self.model).count()

    def save(self, obj):
        try:
            self.session.add(obj)
            self.session.commit()
            return obj
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
