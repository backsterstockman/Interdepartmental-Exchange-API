'''
Модуль-серви с бизнес-логикой
'''


from sqlalchemy.orm import Session
from transaction.repositories.repository import TransactionRepository
from core.crypto import verify_transaction, get_transaction_hash, create_signature, encode_payload, decode_payload
from dto.models import Transaction, Message, TransactionsData, BaseExchangeModel
import datetime

class ExchangeService:
    
    def __init__(self, db: Session):
        self.repo = TransactionRepository(db)


    def process_incoming(self, data: TransactionsData) -> TransactionsData:
        """Логика обработки входящих транзакций и генерации квитков"""
        receipts = []
        for tx in data.Transactions:
            # Валидация по ТЗ
            if not tx.Sign or not verify_transaction(tx):
                continue
            
            # Извлечение сообщения для БД и квитка
            msg = decode_payload(tx.Data, Message)
            self.repo.save(tx, msg.ReceiverBranch, str(msg.ChainGuid))

            # Генерация квитка (тип 215)
            if msg.InfoMessageType != 215:
                receipts.append(self._create_receipt(tx, msg))
        
        return TransactionsData(Transactions=receipts, Count=len(receipts))


    def _create_receipt(self, original_tx: Transaction, original_msg: Message) -> Transaction:
        """
        Создает ответный квиток (сообщение типа 215) на полученную транзакцию.
        
        Квиток подтверждает факт получения сообщения и связывается с ним через 
        ChainGuid и Hash предыдущей транзакции.

        :param original_tx: Транзакция, на которую формируется подтверждение.
        :param original_msg: Распакованное сообщение из исходной транзакции.
        :return: Новая сформированная транзакция с квитком внутри.
        """
        # Формируем полезную нагрузку квитка (бизнес-данные)
        # Согласно ТЗ, квиток должен содержать хэш исходной транзакции
        ticket_payload = {"BankGuaranteeHash": original_tx.Hash}
        
        # 1. Формируем объект Message для квитка
        receipt_msg = Message(
            Data=encode_payload(BaseExchangeModel(**ticket_payload)),
            SenderBranch="SYSTEM_B", # Отправитель квитка — Система Б
            ReceiverBranch="SYSTEM_A", # Получатель квитка — Система А
            InfoMessageType=215, # Тип сообщения: Квиток
            MessageTime=datetime.datetime.now(datetime.timezone.utc),
            ChainGuid=original_msg.ChainGuid, # Сохраняем идентификатор цепочки
            PreviousTransactionHash=original_tx.Hash # Ссылка на исходную транзакцию
        )
        
        # 2. Упаковываем сообщение в транзакцию типа 9
        tx = Transaction(
            TransactionType=9,
            Data=encode_payload(receipt_msg),
            TransactionTime=datetime.datetime.now(datetime.timezone.utc)
        )
        
        # 3. Финализируем транзакцию: вычисляем хэш и накладываем электронную подпись
        tx.Hash = get_transaction_hash(tx)
        tx.Sign = create_signature(tx.Hash)
        
        return tx


    def search_outgoing(self, start, end, limit, offset) -> TransactionsData:
        """
        Выполняет поиск исходящих транзакций в репозитории и упаковывает их в DTO.
        
        Метод реализует логику фильтрации по времени и пагинации, превращая
        объекты БД (SQLAlchemy модели) обратно в транспортные объекты (Pydantic).

        :param start: Начало временного интервала поиска.
        :param end: Конец временного интервала поиска.
        :param limit: Количество записей на страницу.
        :param offset: Смещение для пагинации.
        :return: Объект TransactionsData со списком транзакций и их общим количеством.
        """
        # Запрашиваем данные из репозитория (БД)
        results, total = self.repo.get_outgoing_for_system_a(start, end, limit, offset)
        
        # Трансформируем объекты SQLAlchemy в DTO Transaction
        # Используем item.__dict__, чтобы передать атрибуты модели БД в конструктор Pydantic
        tx_list = [Transaction(**item.__dict__) for item in results]
        
        # Формируем итоговый объект ответа с метаданными о количестве
        return TransactionsData(Transactions=tx_list, Count=total)