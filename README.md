# Wallet API

## Документация

- **Swagger**: [http://78.24.216.113:8010/docs](http://78.24.216.113:8010/docs)
- **ReDoc**: [http://78.24.216.113:8010/redoc](http://78.24.216.113:8010/redoc)

## Описание

Приложение для управления электронными кошельками, построенное на FastAPI и SQLAlchemy, и следующее принципам Domain-Driven Design (DDD).

## Основные функции и ограничения

### Аутентификация и Управление Профилем

- `POST /auth/register`: Регистрация нового пользователя. После регистрации создаются кошельки для всех валют.
- `POST /auth/login`: Вход в систему. Возвращает JWT токен.
- `GET /user/get/id`: Получение информации о текущем пользователе.
- `GET /user/get/token`: Получение информации о пользователе по токену.

### Управление Кошельками

- `GET /user/wallets`: Получение списка всех кошельков текущего пользователя.
- `GET /user/wallet`: Получение деталей конкретного кошелька.
  
### Транзакции и Операции

- `GET /user/transactions`: Получение истории транзакций текущего пользователя. * Currently not work. Founded BUG. Fixing.
- `GET /wallet/transactions`: Получение истории транзакций конкретного кошелька.
- `POST /wallet/deposit`: Внесение средств на кошелек. (без подтверждения)
- `POST /wallet/exchange`: Обмен валют с учетом текущего курса. Разрядность 10 знаков после точки.
- `POST /wallet/transfer`: Перевод средств между кошельками. Возможен перевод на кошелек другого пользователя.
- `POST /wallet/withdraw`: Вывод средств. (не активно)

### Безопасность

- Доступ к операциям с кошельками и транзакциями возможен только после аутентификации.
- Все транзакции являются атомарными: в случае ошибки все изменения откатываются.

## В разработке

- Логика подтверждения операции депозита и вывода через платежные шлюзы.
- Логика перевода средств между пользователями (P2P).
