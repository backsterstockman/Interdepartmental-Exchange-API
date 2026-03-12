'''
Модуль c крипто-функциями и ЭЦП
'''

import base64
import hashlib
import json
from typing import Any

from dto.models import BaseExchangeModel, Transaction


def verify_transaction(tr: Transaction) -> bool:
    '''
    Проверяет валидность транзакции:
    1. Пересчитывает хэш и сверяет с tr.Hash
    2. Пересчитывает подпись и сверяет с tr.Sign
    '''

    #пересчитываем хещ
    expected_hash = get_transaction_hash(tr)

    #сравниваем хеши
    is_hash_valid = tr.Hash and tr.Hash.upper() == expected_hash
    is_sign_valid = tr.Sign

    return bool(is_hash_valid and is_sign_valid)


def encode_payload(model: BaseExchangeModel) -> str:
    """
    Упаковывает любую бизнес-модель в Base64 строку для поля Data.
    Используется перед отправкой.
    """
    json_str = get_canonical_json(model)
    return base64.b64encode(json_str.encode('utf-8')).decode('utf-8')


def decode_payload(payload_base64: str, target_class: type[BaseExchangeModel]) -> Any:
    """
    Распаковывает данные из Base64 обратно в объект Pydantic.
    Используется при получении транзакции из БД или API.
    """
    json_bytes = base64.b64decode(payload_base64)
    #преобразуем json байты в объект и проверяем json
    return target_class.model_validate_json(json_bytes)


def get_canonical_json(tr: Transaction) -> str:
    """
    Превращает модель в каноническую JSON-строку:
    - Без пробелов между ключами и значениями
    - Ключи отсортированы по алфавиту
    - Форматирование дат и чисел берется из нашего serialize_all
    """
    #Приводим модель к json
    data_dict = json.loads(tr.model_dump_json())

    #окончательно преобразуем объект к json
    return json.dumps(
        data_dict,
        sort_keys=True,#сортировка ключей объекта
        ensure_ascii=False,#используем UTF-8
        separators=(',',':')# удаляем пробелы из json, чтобы хеш был правильный
    )


def get_transaction_hash(tr: Transaction) -> str:
    '''
    Ф-ия для получения хеша транзакции
    tr - транзакция
    '''
    #копируем транзакцию, чтобы не менять оригинальную
    tr_copy = tr.model_copy()

    #обнуляем поля, участвующие в записи
    tr_copy.Hash = None
    tr_copy.Sign = None

    tr_copy_json = get_canonical_json(tr_copy)

    #кодируем строку в utf-8 и хешируем при помощи sha256
    hash_object = hashlib.sha256(tr_copy_json.encode('utf-8'))

    #возвращаем хеш в виде строки hex в верхнем регистре
    return hash_object.hexdigest().upper()


def create_signature(hash_hex: str) -> str:
    '''
    Метод для создания ЭЦП
    hash_hex - хеш из ф-ии get_transaction_hash
    '''
    #преобразуем хеш в байты
    hash_bytes = hash_hex.encode('utf-8')

    #преобразуем байты хеша в Base64 и возвращаем как строку
    return base64.b64encode(hash_bytes).decode('utf-8')
