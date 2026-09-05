import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_home(client):
    r = client.get('/')
    assert r.status_code == 200


def test_register_get(client):
    r = client.get('/register')
    assert r.status_code == 200


def test_login_get(client):
    r = client.get('/login')
    assert r.status_code == 200


def test_lessons_get(client):
    r = client.get('/lessons')
    assert r.status_code == 200


def test_lesson_detail(client):
    r = client.get('/lesson/1')
    assert r.status_code in (200, 404)
