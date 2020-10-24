from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import redis

redisConn = redis.StrictRedis(host='localhost', port=6379, db=0)

# Создаем пул соединения с БД
engine = create_engine('mysql://%s:%s@%s/%s?charset=utf8mb4' % ("root", "litva", "mysql", "bitcoin_bot"), encoding=' utf-8',convert_unicode=True, pool_recycle=1800)
db_session = scoped_session(sessionmaker(autocommit=True,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    # Инициализация БД
    import models 
    Base.metadata.create_all(bind=engine)
