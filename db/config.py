'''
Модуль для настройки бд
'''


import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


load_dotenv()


DATABASE_URL = os.getenv('DATABASE_URL')

#создаем движок для бд
engine = create_engine(
    DATABASE_URL,
    # работаем с sqlite, поэтому нужно отключать однопоточность
    connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}
)


#создаем сессию, отключаем автокоммиты и автофлуши, привязываемся к нашему движку
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    '''
    Ф-ия для внедрения зависимости(БД) в роуты
    '''
    db = SessionLocal()
    try:
        yield db #передаем управление в роут
    finally: 
        db.close() #после отработки кода в роуте, закрываем соединение