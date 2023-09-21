import httpx
import pytest
from faker import Faker

fake = Faker()

BASE_URL = "http://0.0.0.0:8010"  

async def register_user(client):
    username = fake.user_name()
    email = fake.email()
    password = fake.password()
    
    response = await client.post(f"{BASE_URL}/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert response.status_code == 200
    
    return username, password

async def get_token(client, username, password):
    response = await client.post(f"{BASE_URL}/auth/login", params={
        "username": username,
        "password": password
    })
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.mark.asyncio
async def test_registration_and_login():
    async with httpx.AsyncClient() as client:
        username, password = await register_user(client)
        token = await get_token(client, username, password)
        assert token
        print(f"User token: {token}")

@pytest.mark.asyncio
async def test_get_wallets():
    async with httpx.AsyncClient() as client:
        username, password = await register_user(client)
        token = await get_token(client, username, password)
        print(f"User token: {token}")
        headers = {"token": f"{token}"}
        response = await client.get(f"{BASE_URL}/user/wallets", headers=headers)
        assert response.status_code == 200
        wallets = response.json()
        print(f"User wallets: {wallets}")
        # можно добавить проверки на содержимое ответа сервера

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


# Добавьте другие тесты по аналогии
