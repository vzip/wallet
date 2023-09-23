import httpx
import pytest
from faker import Faker
from asyncio import gather
import logging
import sys
from datetime import datetime
import pandas as pd



# Настройка логирования
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

fake = Faker()
fakename = fake.first_name_male() #"XteedZsFFSrDDDFGbBrSSAdaat"
fake_email = fake.email() #"xteZddDASFSbFFFGDBdaadst@xddf.com"
fake_password = fake.password(length=40, special_chars=True, upper_case=True) #"XtSedFFSZeDSFbFGDBBaaarcst64434!Z" 
# counter = 0
# Initialize the counter to the current timestamp in seconds
counter = int(datetime.timestamp(datetime.now()))
print(f"{counter}")

BASE_URL = "http://0.0.0.0:8010"  


async def register_user(client):
    global counter
    try:
        username = fakename + str(counter)
        email = str(counter) + fake_email
        password = fake_password + str(counter)
        counter += 1
        
        payload={
            "username": username,
            "email": email,
            "password": password
        }

        logging.info(f"Sending registration data: {payload}") 
        print(f"Sending registration data: {payload}")

        response = await client.post(f"{BASE_URL}/auth/register", json=payload)

        logging.info(f"Received response: {response.status_code}, {response.json()}")
        print(f"Received response: {response.status_code}, {response.json()}")

        assert response.status_code == 200
        
        return username, password
    
    except Exception as e:
            raise Exception(f"Failed with username: {username}, password: {password}") from e
    
async def get_token(client, username, password):
    try:
        response = await client.post(f"{BASE_URL}/auth/login", params={
            "username": username,
            "password": password
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    except Exception as e:
        raise Exception(f"Failed with username: {username}, password: {password} with {str(e)}") from e
    
@pytest.mark.parametrize("task_number, attempts", [(i, 0) for i in range(1, 10)])
@pytest.mark.asyncio
async def test_registration(task_number, attempts):
    async with httpx.AsyncClient(timeout=180.0) as client:
        username, password = None, None  # Инициализация перед блоком try
        try:
            username, password = await register_user(client)
            assert username
            return username, password
        except Exception as e:
            raise Exception(f"Failed with username: {username}, password: {password} with {str(e)}") from e    
    
@pytest.mark.parametrize("task_number, attempts", [(i, 0) for i in range(1, 10)])
@pytest.mark.asyncio
async def test_registration_and_login(task_number, attempts):
    async with httpx.AsyncClient(timeout=360.0) as client:
        username, password = None, None  # Инициализация перед блоком try
        try:
            username, password = await register_user(client)
            token = await get_token(client, username, password)
            assert token
            return username, password
        except Exception as e:
            raise Exception(f"Failed with username: {username}, password: {password} with {str(e)}") from e

@pytest.mark.parametrize("task_number, attempts", [(i, 0) for i in range(1, 10)])
@pytest.mark.asyncio
async def test_wallet_operations(task_number, attempts):
    async with httpx.AsyncClient(timeout=360.0) as client:
        username, password = None, None  # Инициализация перед блоком try
        try:
            username, password = await register_user(client)
            token = await get_token(client, username, password)
            headers = {"token": f"{token}"}

            # Получение начальных кошельков
            response = await client.get(f"{BASE_URL}/user/wallets", headers=headers)
            assert response.status_code == 200
            wallets = response.json()

            # Initial expected balances
            expected_balances = {wallet['id']: float(wallet['balance']) for wallet in wallets["wallets"]}

            # Обмен валют
            for from_currency in [1, 2, 3]:
                for to_currency in [1, 2, 3]:
                    if from_currency != to_currency:
                        response = await client.post(f"{BASE_URL}/wallet/exchange", headers=headers, params={
                            "from_currency": from_currency,
                            "to_currency": to_currency,
                            "amount": 0.05
                        })
                        assert response.status_code == 200
                        exchange_info = response.json()

                        # Update the expected balances based on the exchange info
                        from_wallet_id = next(wallet['id'] for wallet in wallets["wallets"] if wallet['currency_id'] == from_currency)
                        to_wallet_id = next(wallet['id'] for wallet in wallets["wallets"] if wallet['currency_id'] == to_currency)

                        # Update expected balances considering the actual conversion rate
                        expected_balances[from_wallet_id] -= float(exchange_info['amount_int'])
                        expected_balances[to_wallet_id] += float(exchange_info['amount_ext'])

            # Тест перевода денег между кошельками
            for source_wallet in wallets["wallets"]:
                for target_wallet in wallets["wallets"]:
                    if source_wallet['id'] != target_wallet['id']:
                        response = await client.post(f"{BASE_URL}/wallet/transfer", headers=headers, params={
                            "source_wallet_id": source_wallet['id'],
                            "target_wallet_id": target_wallet['id'],
                            "amount": 0.05  # Перевод 100 единиц
                        })
                        assert response.status_code == 200
                        transaction = response.json()
                        print(f"User transaction: {transaction}")

            # Check updated balances
            response = await client.get(f"{BASE_URL}/user/wallets", headers=headers)
            updated_wallets = response.json()["wallets"]
            for wallet in updated_wallets:
                assert round(float(wallet['balance']), 10) == round(expected_balances[wallet['id']], 10)
                print(f"Wallet ID: {wallet['id']}")
                print(f"Expected balance: {round(expected_balances[wallet['id']], 10)}")
                print(f"Actual balance: {float(wallet['balance'])}")

            return username, password
        except Exception as e:
            raise Exception(f"Failed with username: {username}, password: {password}") from e
        
@pytest.mark.parametrize("task_number, attempts", [(i, 0) for i in range(1, 10)])
@pytest.mark.asyncio
async def test_transfer_between_users(task_number, attempts):
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # Создание первого пользователя и получение его кошельков
        username1, password1 = await register_user(client)
        token1 = await get_token(client, username1, password1)
        headers1 = {"token": f"{token1}"}
        response1 = await client.get(f"{BASE_URL}/user/wallets", headers=headers1)
        assert response1.status_code == 200
        wallets1 = response1.json()["wallets"]
        print(f"wallets1: {wallets1}")
            

        # Создание второго пользователя и получение его кошельков
        username2, password2 = await register_user(client)
        token2 = await get_token(client, username2, password2)
        headers2 = {"token": f"{token2}"}
        response2 = await client.get(f"{BASE_URL}/user/wallets", headers=headers2)
        assert response2.status_code == 200
        wallets2 = response2.json()["wallets"]
        print(f"wallets2: {wallets2}")

        # Перевод средств с первого кошелька первого пользователя на первый кошелек второго пользователя
        source_wallet = next(wallet for wallet in wallets1 if wallet['currency_id'] == 1)
        target_wallet = next(wallet for wallet in wallets2 if wallet['currency_id'] == 1)

        transfer_amount = 0.05
        response = await client.post(f"{BASE_URL}/wallet/transfer", headers=headers1, params={
            "source_wallet_id": source_wallet['id'],
            "target_wallet_id": target_wallet['id'],
            "amount": transfer_amount
        })
        assert response.status_code == 200

        # Проверка балансов после перевода
        response1 = await client.get(f"{BASE_URL}/user/wallets", headers=headers1)
        updated_wallets1 = response1.json()["wallets"]
        updated_source_wallet = next(wallet for wallet in updated_wallets1 if wallet['id'] == source_wallet['id'])
        assert round(float(updated_source_wallet['balance']), 10) == round(float(source_wallet['balance']) - transfer_amount, 10)
        print(f"updated_source_wallet: {round(float(updated_source_wallet['balance']), 10)} == source_wallet - transfer_amount: {round(float(source_wallet['balance']) - transfer_amount, 10)}")

        response2 = await client.get(f"{BASE_URL}/user/wallets", headers=headers2)
        updated_wallets2 = response2.json()["wallets"]
        updated_target_wallet = next(wallet for wallet in updated_wallets2 if wallet['id'] == target_wallet['id'])
        assert round(float(updated_target_wallet['balance']), 10) == round(float(target_wallet['balance']) + transfer_amount, 10)
        print(f"updated_target_wallet: {round(float(updated_target_wallet['balance']), 10)} == target_wallet + transfer_amount: {round(float(target_wallet['balance']) + transfer_amount, 10)}")

##  Тест траназакции с учетом подтверждения сервисного юезра 

# Регистрация сервисного пользователя
async def register_service_user(client):
    global counter
    username = fakename + str(counter)
    email = str(counter) + fake_email
    password = fake_password + str(counter)
    counter += 1

    response = await client.post(f"{BASE_URL}/auth/register_service", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert response.status_code == 200
    return response.json()# ["access_token"] ["user_id"]

# Подтверждение депозитной транзакции сервисным пользователем
async def confirm_deposit(client, token, transaction_id):
    response = await client.put(f"{BASE_URL}/service/transaction/deposit", headers={"token": token}, params={
        "transaction_id": transaction_id,
        "new_status": "paid"
    })
    assert response.status_code == 200
    return response.json()


# Создание внешнего кошелька и выполнение запроса на вывод
async def create_external_wallet_and_withdraw(client, user_token, service_token, amount=0.1):
    headers = {"token": f"{user_token}"}

    # Создание внешнего кошелька (предполагаем, что у нас есть такой метод)
    response = await client.post(f"{BASE_URL}/user/create/external_wallet", headers=headers)
    assert response.status_code == 200
    external_wallet = response.json()

    # Получение начальных кошельков
    response = await client.get(f"{BASE_URL}/user/wallets", headers=headers)
    assert response.status_code == 200
    wallets = response.json()

    # Здесь надо взять кошелек 0 и дальше его использовать как from_wallet
    from_wallet = wallets["wallets"][0] 

    # Выполнение запроса на вывод на внешний кошелек
    deposit_headers = {"token": f"{service_token}"}
    response = await client.post(f"{BASE_URL}/wallet/withdraw", headers=deposit_headers, params={
        "service_user_id": service_token,  # это ID сервисного пользователя
        "wallet_id": from_wallet["id"],
        "amount": amount
    })
    assert response.status_code == 200
    withdraw_transaction = response.json()

    return withdraw_transaction["transaction_id"]


# Создание запроса на пополнение
async def create_deposit(client, user_token, service_user_id, amount=0.1):
    headers = {"token": f"{user_token}"}

    # Получение начальных кошельков
    response = await client.get(f"{BASE_URL}/user/wallets", headers=headers)
    assert response.status_code == 200
    wallets = response.json()

    # Здесь надо взять кошелек 0 и дальше его использовать как to_wallet
    to_wallet = wallets["wallets"][0] 

    response = await client.post(f"{BASE_URL}/wallet/deposit", headers=headers, params={
        "service_user_id": service_user_id,  
        "wallet_id": to_wallet["id"],
        "amount": amount
    })
    assert response.status_code == 200
    deposit_transaction = response.json()

    return deposit_transaction["id"]
@pytest.mark.parametrize("task_number, attempts", [(i, 0) for i in range(1, 10)])
@pytest.mark.asyncio
async def test_wallet_operations_with_service_user(task_number, attempts):
    async with httpx.AsyncClient(timeout=360.0) as client:
        # 1. Регистрация и вход сервисного пользователя
        service = await register_service_user(client)
        service_token = service["access_token"]
        print(f"service_token: {service_token}")
        service_user_id = service["user_id"]
        print(f"service_user_id: {service_user_id}")

        # 2. Регистрация и вход обычного пользователя
        username, password = await register_user(client)
        user_token = await get_token(client, username, password)
        print(f"user_token: {user_token}")

        # 3. Создание транщакции запроса на депозит
        transaction_id = await create_deposit(client, user_token, service_user_id)
        print(f"Deposit transaction_id: {transaction_id}")

        # 4. Подтверждение депозитной транзакции сервисным пользователем
        confirm_response = await confirm_deposit(client, service_token, transaction_id)
        assert confirm_response
        print(f"Confirmed transaction: {confirm_response}")

# TODO: Добавить другие тесты 

# flow extension 



report = []  # Сюда будем записывать результаты тестов test_wrapper

async def wrapper(task, task_number, attempts):
    username, password = None, None  # Инициализация

    for attempt in range(3):  # Попытаемся выполнить задачу 3 раза
        attempts += 1
        try:
            username, password = await task(task_number, attempts)
            report.append({
                "task": task.__name__, 
                "status": "success", 
                "task_number": task_number, 
                "attempts": attempts,
                "username": username,
                "password": password
                })
            break  # Выход из цикла если задача выполнена успешно
        except Exception as e:  # Замените на более конкретный тип исключения, если возможно
            if "500" in str(e):  # Проверка на ошибку 500
                report.append({
                    "task": task.__name__, 
                    "status": f"failed, attempt {attempt}", 
                    "task_number": task_number, 
                    "attempts": attempts,
                    "username": username,
                    "password": password
                    })
            else:
                report.append({
                    "task": task.__name__, 
                    "status": "failed", 
                    "task_number": task_number, 
                    "attempts": attempts,
                    "username": username,
                    "password": password, 
                    "Error": str(e)})
                # break  # Выход из цикла если возникла не ошибка 500 

@pytest.mark.asyncio
async def test_wrapper_400rps():
    tasks_one = [wrapper(test_registration, i, 0) for i in range(1, 100)]
    tasks_two = [wrapper(test_registration, i, 0) for i in range(1, 100)]
    tasks_three = [wrapper(test_registration_and_login, i, 0) for i in range(1, 100)]
    tasks_four = [wrapper(test_registration_and_login, i, 0) for i in range(1, 100)]
    all_tasks = tasks_one + tasks_two + tasks_three + tasks_four
    test = await gather(*all_tasks)
    assert test
    #print(report)

    # Преобразование списка словарей в датафрейм
    df = pd.DataFrame(report)

    # Сортировка по номеру задачи
    df = df.sort_values('task_number')

    # Сохранение в Excel-файл
    df.to_excel('test_report.xlsx', index=False)