import requests
from flask import json

BASE_URL = "http://localhost:5000"


def test_login():
    print("\nTesting /login")

    correct_data = {
        "email": "withoutpessimism@gmail.com",
        "password": "123456",
    }
    response = requests.post(f"{BASE_URL}/login", json=correct_data)
    print("Response:", response.json())

def test_list_auctions():
    print("\nTesting /auctions")
    response = requests.get(f"{BASE_URL}/auctions")
    print("Response:" ,response.json())
    

if __name__ == "__main__":
    test_list_auctions()
    test_login()