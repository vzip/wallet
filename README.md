# Wallet API

## Документация

- **Swagger**: [http://wallet.doweb.online/docs](http://wallet.doweb.online/docs)
- **ReDoc**: [http://wallet.doweb.online/redoc](http://wallet.doweb.online/redoc)

## Run tests
- **TestsLocal**: [http://wallet.doweb.online/run-tests-local](http://wallet.doweb.online/run-tests-local)
- **TestsDomain**: [http://wallet.doweb.online/run-tests](http://wallet.doweb.online/run-tests)

## Описание

Приложение для управления электронными кошельками, построенное на FastAPI и SQLAlchemy, и следующее принципам Domain-Driven Design (DDD).

## Основные функции и ограничения

### Аутентификация и управление профилем пользователя

- `POST /auth/register`: Регистрация нового пользователя. После регистрации создаются кошельки для всех валют.
- `POST /auth/login`: Вход в систему. Возвращает JWT токен.
- `GET /user/get/id`: Получение id пользователя.
- `GET /user/get/token`: Получение информации о пользователе по токену.

### Управление кошельками пользователя

- `GET /user/wallets`: Получение списка всех кошельков текущего пользователя.
- `GET /user/wallet`: Получение деталей конкретного кошелька.
- `POST /user/create/external_wallet` : Создание внешнего счета-кошелька к которому может быть создана и привязана карта эмитента в системе для вывода средств.
  
### Транзакции и операции пользователя

- `GET /user/transactions`: Получение истории транзакций текущего пользователя.
- `GET /wallet/transactions`: Получение истории транзакций конкретного кошелька.
- `POST /wallet/deposit`: Внесение средств на кошелек через создание транзакции со статусом `pending`, ожидающей смены статуса на `paid` или `reject` со стороны внешнего сервиса.
- `POST /wallet/exchange`: Обмен валют с учетом текущего курса. Разрядность 10 знаков после точки.
- `POST /wallet/transfer`: Перевод средств между кошельками. Возможен перевод на кошелек другого пользователя.
- `POST /wallet/withdraw`: Вывод средств. (не активно)

### Сервисные транзакции и операции 

- `GET /service/auth/login` :  Вход в систему через сервис. Возвращает JWT токен.
- `POST /auth/register_service` : Регистрация сервисного пользователя.
- `PUT/service/transaction/deposit` : Update Service Deposit Transaction Status. Обновление статуса pending транзакций пользователя. Проведение операций двиджения денежных средств. Cоздание сервисной транзакции `deposit` для пополнения сервисного кошелька, создание транзакции `transfer` для перемещения средств с сервисного кошелька на кошелек пользователя, и создание тразакции `comission` для перемещения суммы комиссии с кошеька пользователя на сервисный кошелек.
- `PUT/service/transaction/withdraw` : Update Service Withdraw Transaction Status. Обновление статуса pending транзакций пользователя. Проведение операций двиджения денежных средств. Cоздание транзакции `withdraw` для вывода средств с кошелька пользователя, и создание тразакции `comission` для перемещения суммы комиссии с кошеька пользователя на сервисный кошелек.

### Безопасность

- Доступ к операциям с кошельками и транзакциями возможен только после аутентификации.
- Все транзакции являются атомарными: в случае ошибки все изменения откатываются.

## Логика

- Требуется обновление статуса pending транзакции для проведения операции депозита на кошельки пользователя и сервисного пользователя.

## В разработке

- Логика вывода через платежные шлюзы.
- Логика перевода средств между пользователями (P2P).

## Запустить локально 
- gunicorn (`-w N` -количество воркеров = ядер cpu)  
    gunicorn -w 4 -k uvicorn.workers.UvicornWorker -t 120 main:app --bind 0.0.0.0:8010
- uvicorn
    uvicorn main:app --host 0.0.0.0 --port 8010

## Run with docker 
- docker network create wallet_network 
- docker build --no-cache -t wallet . 
- docker run --name psql --network=wallet_network --env-file .env -p 5432:5432 -d --restart=always postgres:14
- docker run --name wallet --network=wallet_network --env-file .env -p 8010:8010 -d --restart=always wallet


