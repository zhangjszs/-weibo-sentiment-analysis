from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

from config.settings import Config

engine = create_engine(
    Config.get_database_url(),
    pool_size=Config.DB_POOL_SIZE,
    max_overflow=20,
    pool_recycle=Config.DB_POOL_RECYCLE,
    pool_pre_ping=True,
)

db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    Base.metadata.create_all(bind=engine)
