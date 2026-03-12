'''
Модуль с вспомогательными функциями
'''

import datetime
import uuid

from core.crypto import create_signature, encode_payload, get_transaction_hash
from db.config import Base, SessionLocal, engine
from db.models import DBTransaction
from dto.models import BaseExchangeModel, Message, Transaction
from transaction.repositories.repository import TransactionRepository


def init_db():
    """Инициализация БД: создание таблиц и добавление первой транзакции."""
    # 1. Создаем таблицы, если их нет
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 2. Проверяем, есть ли уже записи
        exists = db.query(DBTransaction).first()
        if not exists:
            print("База пуста. Создаем приветственную транзакцию...")
            
            repo = TransactionRepository(db)
            
            # Создаем полезную нагрузку (бизнес-данные)
            payload = BaseExchangeModel(info="Genesis Block / Initial Transaction")
            
            # Создаем Message (Сообщение)
            msg = Message(
                Data=encode_payload(payload),
                SenderBranch="SYSTEM_B",
                ReceiverBranch="SYSTEM_A",
                InfoMessageType=1, # Тип: Инициализация
                MessageTime=datetime.datetime.now(datetime.timezone.utc),
                ChainGuid=uuid.uuid4()
            )
            
            # Создаем Transaction (Транзакция)
            tx_dto = Transaction(
                TransactionType=1,
                Data=encode_payload(msg),
                TransactionTime=datetime.datetime.now(datetime.timezone.utc)
            )
            
            # Вычисляем хэш и подпись
            tx_dto.Hash = get_transaction_hash(tx_dto)
            tx_dto.Sign = create_signature(tx_dto.Hash)
            
            # Сохраняем в БД через репозиторий
            repo.create(
                tx_dto=tx_dto, 
                receiver_branch=msg.ReceiverBranch, 
                chain_guid=str(msg.ChainGuid)
            )
            print(f"Первая транзакция создана с хэшем: {tx_dto.Hash}")
            
    finally:
        db.close()