Interdepartmental Exchange API (System B) — LIVE DEMO
Данный сервис является реализацией Системы Б в рамках протокола межведомственного обмена данными. Приложение имитирует работу реестра банковских гарантий с проверкой цифровых подписей и автоматическим квитированием.

🔗 Попробовать API (Swagger UI): https://interdepartmental-exchange-api-production.up.railway.app/docs

🛠 Что это и как работает?
Приложение реализует сложную логику «матрешки», где бизнес-данные (информация о гарантии) упаковываются в сообщение, сообщение — в транзакцию, а транзакция — в транспортный конверт API. На каждом этапе используется Base64-кодирование и контроль целостности.

Основные функции:
Контроль хэшей: Проверка SHA-256 (HEX Upper Case) для каждой входящей транзакции.

Эмуляция ЭЦП: Проверка подписи на основе хэша данных.

Авто-квитирование: На каждое валидное входящее сообщение сервис мгновенно генерирует ответный квиток (тип 215) с подтверждением.

Живая база данных: Все отправленные вами сообщения сохраняются в реестре и доступны для поиска.

🚀 Как потрогать API (Quick Start)
Поскольку всё уже настроено и запущено, вы можете протестировать основные методы прямо сейчас в интерфейсе Swagger:

1. Проверка исходящих (Outgoing)
Этот метод имитирует получение Системой А новых сообщений из реестра.

Откройте метод POST /api/messages/outgoing.

Нажмите Try it out.

Вставьте в поле Data следующий поисковый запрос (это Base64-фильтр по датам):

'''
{
  "Data": "eyJTdGFydERhdGUiOiAiMjAyMC0wMS0wMVQwMDowMDowMFoiLCAiRW5kRGF0ZSI6ICIyMDI3LTEyLTMxVDIzOjU5OjU5WiIsICJMaW1pdCI6IDEwLCAiT2Zmc2V0IjogMH0=",
  "Sign": "STUB",
  "SignerCert": "STUB"
}
'''

Нажмите Execute. Вы получите список транзакций, включая тестовую гарантию из "Примера 1".

2. Отправка сообщения (Incoming)
Этот метод имитирует подачу нового сообщения в реестр.

Откройте метод POST /api/messages/incoming.

Нажмите Try it out.

Чтобы не вычислять хэш вручную, используйте этот готовый пакет:

'''
{
  "Data": "eyJUcmFuc2FjdGlvbnMiOiBbeyJUcmFuc2FjdGlvblR5cGUiOiA5LCAiRGF0YSI6ICJleUpKWW01dmJtVjBkV0ZzYVhSNVpDSTZNakF4TENKSmJtTm9iV1Z6Y21GaGRHVnpaVDBpVjlsZFlXUmhJR2RoY21GdWRHbGxJam9nSWpBZ2V3PT0iLCAiSGFzaCI6ICJCOEUxMEY2OTVEOUQ3RERCOENBODFDRUNBOTBDRjg0RTQwOTJGMThBQjAzNTM5OThFNDBBRkRBMTBGMzQxODAxIiwgIlNpZ24iOiAiUWpneU1UQUdOalkxUkRreVJFUkNRME5CT0VGRE5VTkJPVEJEUmpnME5VUTFNbVl6T0VFeU16VXpPVGhoT0VSR1JFUkJNVEJHTXpReE9EQXhJZz09IiwgIlNpZ25lckNlcnQiOiAiU1RVQiIsICJUcmFuc2FjdGlvblRpbWUiOiAiMjAyNC0wNS0yMFQxMDowMDowMFoifV0sICJDb3VudCI6IDF9",
  "Sign": "STUB",
  "SignerCert": "STUB"
}
'''

Нажмите Execute. В ответ сервис вернет вам сгенерированный квиток подтверждения.

🏗 Техническая справка
Проект построен на FastAPI и SQLAlchemy. В качестве хранилища используется SQLite.

Алгоритм проверки данных:

Десериализация конверта SignedApiData.

Декодирование Data из Base64 в объект транзакций.

Очистка полей Hash и Sign в транзакции для проверки целостности.

Сравнение присланного хэша с вычисленным по правилам SHA-256 (JSON без пробелов, сортировка ключей).