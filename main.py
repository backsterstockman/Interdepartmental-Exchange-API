'''
Модуль инициализации и запуска приложения
'''


from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

from api.routes import router
from db.config import engine, Base
from utils import init_db


Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    '''
    Метод, представляющий собой жизненный цикл приложения
    '''

    print('Приложение запущено')
    init_db()
    yield
    print('Приложение закончило свою работу')


app = FastAPI(
    title='Interagency Exchange System API',
    description='Система Б (Центральный реестр)',
    version='1.0.0',
    lifespan=lifespan
)

#подключаем роутет
app.include_router(router)

if __name__ == '__main__':
    #запускаем приложение на uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)