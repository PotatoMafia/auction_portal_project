import logging

import pytest
from app import app, db
from models import User, Auction, Bid
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auction_test.db'
    app.config['JWT_SECRET_KEY'] = 'AAAAAAAAAAAAAAA'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


# Fixture for admin token
@pytest.fixture
def admin_token1():
    with app.app_context():
        try:
            user = User(email="admin@test.com", username="admin", role="admin")
            user.set_password("password")
            db.session.add(user)
            db.session.commit()
            token = create_access_token(identity=user.user_id, additional_claims={'role': 'admin'})
            return token
        except Exception as e:
            logging.error(f"Error creating admin token: {e}")
            raise

# Test user registration
def test_register_user(client):
    response = client.post('/register', json={
        "email": "newuser@test.com",
        "username": "newuser",
        "password": "password"
    })
    assert response.status_code == 201
    assert response.json['message'] == 'User registered successfully'

# Test user login
def test_login_user(client):
    with app.app_context():
        user = User(email="newuse@test.com", username="newuse")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

    response = client.post('/login', json={
        "email": "newuse@test.com",
        "password": "password"
    })
    assert response.status_code == 200
    assert 'access_token' in response.json

# Test admin login
def test_login_admin(client):
    with app.app_context():
        user = User(email="newuse@test.com", username="newuse", role="admin")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

    response = client.post('/login', json={
        "email": "newuse@test.com",
        "password": "password"
    })

    assert response.status_code == 200
    assert 'access_token' in response.json
    assert response.json['role'] == 'admin'
    assert response.json['username'] == 'newuse'
    token = response.json['access_token']
    return token

# Test auction creation by admin
def test_create_auction(client):
    token = test_login_admin(client)

    with open('test_image.png', 'wb') as f:
        f.write(b"Test image content")

    with open('test_image.png', 'rb') as image_file:
        response = client.post('/admin/auction', headers={
            "Authorization": f"Bearer {token}"
        }, data={
            "title": "Test Auction",
            "description": "Test description",
            "starting_price": 100,
            "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "end_time": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            "user_id": 1,
            "status": "aktywny"
        }, content_type='multipart/form-data')

    print("Response Data:", response.data)
    print("Response JSON:", response.json)

    assert response.status_code == 201


def test_get_auctions(client):
    response = client.get('/auctions')
    assert response.status_code == 200
    assert isinstance(response.json, list)

