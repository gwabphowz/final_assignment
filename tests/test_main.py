import os
import pytest
from main import app, db
from models import User


@pytest.fixture
def client():
    app.config['TESTING'] = True
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    client = app.test_client()

    cleanup()  # clean up before every test

    db.create_all()

    yield client


def cleanup():
    # clean up the DB (drop all tables)
    db.drop_all()


def test_index_not_logged_in(client):
    response = client.get('/')
    assert b'Enter your name' in response.data
    assert response.status_code == 200  # 200 means success. See: https://en.wikipedia.org/wiki/List_of_HTTP_status_codes


def test_index_logged_in(client):
    client.post('/login', data={"user-name": "Test User", "user-email": "test@user.com",
                                "user-password": "password123"}, follow_redirects=True)
    
    response = client.get('/')
    assert b'Enter your guess' in response.data
    # assert response.status_code == 200


def test_result_correct(client):
    # create a user
    client.post('/login', data={"user-name": "Test User", "user-email": "test@user.com",
                                "user-password": "password123"}, follow_redirects=True)

    # get the first (and only) user object from the database
    user = db.query(User).first()
    
    # set the secret number to 22, so that you can make a success "guess" in the test.
    user.secret_number = 22
    db.add(user)
    db.commit()

    response = client.post('/result', data={"guess": 22})  # enter the correct guess
    assert b'Correct! The secret number is 22' in response.data


def test_result_incorrect_try_bigger(client):
    # create a user
    client.post('/login', data={"user-name": "Test User", "user-email": "test@user.com",
                                "user-password": "password123"}, follow_redirects=True)

    # get user object from the database
    user = db.query(User).first()

    user.secret_number = 22
    db.add(user)
    db.commit()

    response = client.post('/result', data={"guess": 13})  # enter the wrong guess (too small)
    assert b'Your guess is not correct... try something bigger.' in response.data


def test_result_incorrect_try_smaller(client):
    # create a user
    client.post('/login', data={"user-name": "Test User", "user-email": "test@user.com",
                                "user-password": "password123"}, follow_redirects=True)

    # get user object from the database
    user = db.query(User).first()

    user.secret_number = 22
    db.add(user)
    db.commit()

    response = client.post('/result', data={"guess": 27})  # enter the wrong guess (too big)
    assert b'Your guess is not correct... try something smaller.' in response.data


def test_profile(client):
    # create a user
    client.post('/login', data={"user-name": "Test User", "user-email": "test@user.com",
                                "user-password": "password123"}, follow_redirects=True)

    response = client.get('/profile')
    assert b'Test User' in response.data


def test_profile_edit(client):
    # create a user
    client.post('/login', data={"user-name": "Test User", "user-email": "test@user.com",
                                "user-password": "password123"}, follow_redirects=True)

    # GET
    response = client.get('/profile/edit')
    assert b'Edit your profile' in response.data

    # POST
    response = client.post('/profile/edit', data={"profile-name": "Test User 2",
                                                  "profile-email": "test2@user.com"}, follow_redirects=True)

    assert b'Test User 2' in response.data
    assert b'test2@user.com' in response.data


def test_profile_delete(client):
    # create a user
    client.post('/login', data={"user-name": "Test User", "user-email": "test@user.com",
                                "user-password": "password123"}, follow_redirects=True)

    # GET
    response = client.get('/profile/delete')
    assert b'Delete your profile' in response.data

    # POST
    response = client.post('/profile/delete', follow_redirects=True)
    assert b'Enter your name' in response.data  # redirected back to the index site


def test_all_users(client):
    response = client.get('/users')
    assert b'<h3>Users</h3>' in response.data
    assert b'Test User' not in response.data  # Test User is not yet created

    # create a new user
    client.post('/login', data={"user-name": "Test User", "user-email": "test@user.com",
                                "user-password": "password123"}, follow_redirects=True)

    response = client.get('/users')
    assert b'<h3>Users</h3>' in response.data
    assert b'Test User' in response.data


def test_user_details(client):
    # create a new user
    client.post('/login', data={"user-name": "Test User", "user-email": "test@user.com",
                                "user-password": "password123"}, follow_redirects=True)

    # get user object from the database
    user = db.query(User).first()

    response = client.get('/user/{}'.format(user.id))
    assert b'test@user.com' in response.data
    assert b'Test User' in response.data
