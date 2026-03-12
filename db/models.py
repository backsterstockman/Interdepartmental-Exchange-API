from sqlalchemy import Column, String, Integer, DateTime, Text
from db.config import Base


class DBTransaction(Base):
    """
    SQL-таблица для хранения транзакций. 
    Поля дублируют DTO, но с индексами для поиска.
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    TransactionType = Column(Integer)
    Data = Column(Text)  # Base64 строка сообщения
    Hash = Column(String, unique=True, index=True)
    Sign = Column(String)
    SignerCert = Column(String)
    TransactionTime = Column(DateTime, index=True)
    
    # Поля для фильтрации из ТЗ (вынесены из JSON для скорости)
    ReceiverBranch = Column(String, index=True)
    ChainGuid = Column(String, index=True)