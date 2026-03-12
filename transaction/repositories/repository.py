'''
Модуль, реализующий паттерн репозиторий
(по факту должен быть базовый репозиторий, от которого мы наследуемся,
но в данном случае это избыточно,
потому что у нас всего одна модель в бд)
'''

import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func
from db.models import DBTransaction
from dto.models import Transaction

class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db


    def create(self, tx_dto: Transaction, receiver_branch: str, chain_guid: str):
        """
        Сохраняет транзакцию в базу данных
        :param tx_dto: Объект Pydantic-модели Transaction, содержащий данные для сохранения.
        :param receiver_branch: Строковой идентификатор филиала-получателя (извлеченный из Message).
        :param chain_guid: Уникальный глобальный идентификатор цепочки сообщений (UUID).
        :return: Объект DBTransaction, сохраненный в базе данных.
        """
        #создаем объект транзакции
        db_tx = DBTransaction(
            TransactionType=tx_dto.TransactionType,
            Data=tx_dto.Data,
            Hash=tx_dto.Hash,
            Sign=tx_dto.Sign,
            SignerCert=tx_dto.SignerCert,
            TransactionTime=tx_dto.TransactionTime,
            ReceiverBranch=receiver_branch,
            ChainGuid=chain_guid
        )
        #добавляем объект в соединение
        self.db.add(db_tx)
        #подтверждаем изменение
        self.db.commit()
        #обновляем состояние объекта
        self.db.refresh(db_tx)
        return db_tx


    def get_outgoing_for_system_a(self, start: datetime.datetime, end: datetime.datetime, limit: int, offset: int):
        """
        Реализация поиска по ТЗ:
        :param db: Текущая сессия подключения к БД (SQLAlchemy Session).
        :param start: Начальная дата и время интервала поиска (включительно).
        :param end: Конечная дата и время интервала поиска (включительно).
        :param limit: Максимальное количество записей для возврата (размер страницы).
        :param offset: Количество записей, которые нужно пропустить (смещение от начала).
        :return: Кортеж из (список найденных DBTransaction, общее количество записей без учета пагинации).
        """

        #запрос в бд
        query = self.db.query(DBTransaction).filter(
            and_(
                DBTransaction.ReceiverBranch == "SYSTEM_A",
                DBTransaction.TransactionTime >= start,
                DBTransaction.TransactionTime <= end
            )
        )
        
        total_count = query.count()  # Для поля Count в ответе
        #отсекаем значения по пагинации
        results = query.offset(offset).limit(limit).all()
        
        return results, total_count