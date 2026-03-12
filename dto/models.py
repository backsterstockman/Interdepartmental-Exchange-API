'''
Модуль описывающий модели запросов и ответов,
представленных в ТЗ
Имена полей классов указаны точь-в-точь как в ТЗ вместо
правильного snake_case во избежание путаницы
'''

from decimal import Decimal
from typing import Optional

from pydantic import UUID4, BaseModel, ConfigDict, Field, field_serializer
import datetime


class BaseExchangeModel(BaseModel):
    '''
    Базовая модель с настройкой времени в формате UTC ISO 8601
    и приведением Decimal к двум знакам после запятой
    Далее все модели наследуются от нее
    '''
    #позволяет нам обращаться как к переменным, так и к их псевдонимам
    model_config = ConfigDict(populate_by_name=True)


    # * говорит, что мы берем все поля
    # mode='plain' - передача управления нам, отмена стандартной
    # логики сериализации Pydantic
    # check_fields=True, потому что в базовом классе нет полей,
    # а проверяем мы дочерние
    @field_serializer('*', mode='plain', check_fields=False)
    def serialize_all(self, value, _info):
        '''
        Сериализатор, который проверяет все поля
        value - поле класса
        _info - стандартный параметр сериализатора pydantic
        '''
        #если поле - это время
        if isinstance(value, datetime.datetime):
            #то возвращаем время в таком формате
            return value.strftime('%Y-%m-%dT%H:%M:%SZ')
        #если поле - это Decimal, то есть, деньги
        if isinstance(value, Decimal):
            #то ограничиваем его двумя символами после точки
            return str(value.quantize(Decimal('1.00')))
        return value


class SignedApiData(BaseExchangeModel):
    '''
    Объект-конверт для запросов и ответов API.
    Data - json-данные в Base64
    Sign - ЭЦП
    SignerCert - СОК автора организации
    '''
    Data: str
    Sign: str
    SignerCert: str


class Transaction(BaseExchangeModel):
    """
    Модель для описания транзакции
    TransactionType - тип транзакции
    Data - json-пакет типа Message
    Hash - хеш транзакции
    Sign - ЭЦП автора транзакции
    SignerCert - СОК автора транзакции
    TransactionTime - Дата создания транзакции в UTC
    Metadata - Метаданные для быстрого поиска
    TransactionIn - Предыдущая транзакция
    TransactionOut - След. транзакция

    Hash, Sign и SignerCert по умолчанию пустые
    для того, чтобы создать пустой объект Transaction
    и высчитать от него эти поля
    """
    TransactionType: int
    Data: str
    Hash: str = None
    Sign: str = None
    SignerCert: str = ''
    TransactionTime: datetime.datetime
    Metadata: Optional[str] = None
    TransactionIn: Optional[str] = None
    TransactionOut: Optional[str] = None


class Message(BaseExchangeModel):
    """
    Модель информационного сообщения (Таблица 3)
    Data - Base64 от JSON-пакета бизнес-данных (напр. GuaranteeMessage)
    SenderBranch - Филиал отправителя
    ReceiverBranch - Филиал получателя
    InfoMessageType - Тип информационного сообщения (201, 215 и т.д.)
    MessageTime - Время создания сообщения
    ChainGuid - Глобальный уникальный идентификатор цепочки
    PreviousTransactionHash - Хеш предыдущей транзакции в цепочке
    Metadata - Дополнительные метаданные
    """
    Data: str
    SenderBranch: str
    ReceiverBranch: str
    InfoMessageType: int
    MessageTime: datetime.datetime
    ChainGuid: UUID4
    PreviousTransactionHash: Optional[str] = None
    Metadata: Optional[str] = None


class Tax(BaseExchangeModel):
    """
    Объект налога (Таблица 4.1.1)
    Number - Порядковый номер
    NameTax - Наименование налога
    Amount - Сумма налога (Decimal для точности)
    PennyAmount - Сумма пени
    """
    Number: str
    NameTax: str
    Amount: Decimal
    PennyAmount: Decimal


class Obligation(BaseExchangeModel):
    """
    Сведения об обязательствах (Таблица 4.1)
    Type - Тип обязательства
    StartDate - Дата начала
    EndDate - Дата окончания
    ActDate - Дата акта
    ActNumber - Номер акта
    Taxs - Список налогов (объекты Tax)
    """
    Type: int = Field(..., ge=1, le=4)#ограничиваем значения от 1 до 4
    StartDate: Optional[datetime.datetime] = None
    EndDate: Optional[datetime.datetime] = None
    ActDate: datetime.datetime
    ActNumber: str
    Taxs: list[Tax] = Field(default_factory=list)#создаем новый список каждый раз при создании объекта


class GuaranteeMessage(BaseExchangeModel):
    """
    Сообщение о выдаче гарантии (Таблица 4, тип 201)
    InformationType - Всегда 201
    InformationTypeString - "Выдача гарантии"
    Number - Номер гарантии
    IssuedDate - Дата выдачи
    Guarantor - Гарант (Наименование организации)
    Beneficiary - Бенефициар
    Principal - Принципал
    Obligations - Список обязательств (Obligation)
    StartDate/EndDate - Срок действия гарантии
    CurrencyCode/Name - Валюта (код и название)
    Amount - Общая сумма гарантии
    RevokationInfo - Сведения об отзывности
    ClaimRightTransfer - Сведения о передаче прав требования
    PaymentPeriod - Срок оплаты
    SignerName - ФИО подписанта
    AuthorizedPosition - Должность подписанта
    BankGuaranteeHash - Хеш-сумма самой гарантии
    """
    InformationType: int = 201
    InformationTypeString: str = 'Выдача гарантии'
    Number: str
    IssuedDate: datetime.datetime
    Guarantor: str
    Beneficiary: str
    Principal: str
    Obligations: list[Obligation] = Field(default_factory=list)
    StartDate: datetime.datetime
    EndDate: datetime.datetime
    CurrencyCode: str
    CurrencyName: str
    Amount: Decimal
    RevokationInfo: str
    ClaimRightTransfer: str
    PaymentPeriod: str
    SignerName: str
    AuthorizedPosition: str
    BankGuaranteeHash: str


class AccessGuaranteeMessage(BaseExchangeModel):
    """
    Сообщение о принятии гарантии (Тип 210)
    Name - Наименование документа
    BankGuaranteeHash - Хеш гарантии, которую принимают
    Sign - Подпись принятия
    SignerCert - Сертификат подписанта
    """
    Name: str
    BankGuaranteeHash: str
    Sign: str
    SignerCert: str


class DeclineAccessGuaranteeMessage(BaseExchangeModel):
    """
    Сообщение об отказе в принятии (Тип 211)
    Name - Наименование документа
    BankGuaranteeHash - Хеш гарантии
    Sign - Подпись отказа
    SignerCert - Сертификат
    Reason - Причина отказа
    """
    Name: str
    BankGuaranteeHash: str
    Sign: str
    SignerCert: str
    Reason: str


class TicketAboutReceiving(BaseExchangeModel):
    """
    Квиток о получении (Таблица 7, тип 215)
    BankGuaranteeHash - Хеш полученной гарантии
    """
    BankGuaranteeHash: str


class SearchRequest(BaseExchangeModel):
    """
    Модель запроса на поиск транзакций (Таблица 8)
    StartDate/EndDate - Временной интервал поиска
    Limit - Количество записей
    Offset - Смещение (для пагинации)
    """
    StartDate: datetime.datetime
    EndDate: datetime.datetime
    Limit: int
    Offset: int


class TransactionsData(BaseExchangeModel):
    """
    Ответ на запрос поиска (Таблица 9)
    Transactions - Список найденных транзакций (Transaction)
    Count - Общее количество записей в базе
    """
    Transactions: list[Transaction] = Field(default_factory=list)
    Count: int
