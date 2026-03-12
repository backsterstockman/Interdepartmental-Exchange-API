'''
Модуль с путями API
'''

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.config import get_db
from dto.models import (
    SignedApiData, SearchRequest, TransactionsData, 
)
from core.crypto import (
    encode_payload, decode_payload
)
from services.exchange_service import ExchangeService


#объект, включающий все маршруты после api/
router = APIRouter(prefix='/api')


@router.get('/health')
async def health_check():
    '''
    Проверка доступности сервиса
    Возвращает статус 200 и текст "ОК"
    Или ошибку при недоступности сервиса
    '''
    return 'ОК'


@router.post("/messages/outgoing", response_model=SignedApiData)
async def get_messages(envelope: SignedApiData, db: Session = Depends(get_db)):
    """
    Эндпоинт для получения исходящих сообщений (запросов), адресованных Системе А.
    
    Метод извлекает поисковые критерии из зашифрованного/закодированного поля Data,
    выполняет поиск в реестре и возвращает сформированный пакет транзакций.

    :param envelope: Конверт SignedApiData, содержащий в Data SearchRequest (Base64).
    :param db: Сессия базы данных, предоставляемая DI-контейнером FastAPI.
    :return: SignedApiData с упакованным объектом TransactionsData в поле Data.
    """
    service = ExchangeService(db)
    # Декодируем SearchRequest из Base64 поля Data
    req = decode_payload(envelope.Data, SearchRequest)
    
    # Поиск транзакций с учетом фильтров и пагинации
    data = service.search_outgoing(req.StartDate, req.EndDate, req.Limit, req.Offset)
    
    # Возвращаем результат, упакованный обратно в транспортный конверт
    return SignedApiData(
        Data=encode_payload(data), 
        Sign="STUB", 
        SignerCert="STUB"
    )


@router.post("/messages/incoming", response_model=SignedApiData)
async def post_messages(envelope: SignedApiData, db: Session = Depends(get_db)):
    """
    Эндпоинт для приема новых сообщений (транзакций) от Системы А в Систему Б.
    
    Выполняет проверку целостности (хэш) и подписи каждой входящей транзакции, 
    сохраняет их в реестр и автоматически генерирует ответные квитки (тип 215) 
    для подтверждения получения.

    :param envelope: Конверт SignedApiData, содержащий в Data TransactionsData (Base64).
    :param db: Сессия базы данных, предоставляемая DI-контейнером FastAPI.
    :return: SignedApiData, содержащий массив сгенерированных квитков (TransactionsData).
    """
    service = ExchangeService(db)
    # Декодируем список входящих транзакций
    incoming_data = decode_payload(envelope.Data, TransactionsData)
    
    # Обработка: валидация, сохранение и генерация квитков
    receipts_data = service.process_incoming(incoming_data)
    
    # Возврат квитков Системе А для завершения цикла обмена
    return SignedApiData(
        Data=encode_payload(receipts_data), 
        Sign="STUB", 
        SignerCert="STUB"
    )