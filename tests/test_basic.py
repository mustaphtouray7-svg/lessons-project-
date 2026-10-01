import pytest
from app import app, db, Lesson, User, normalize_database_url, serializer


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


def test_postgresql_url_normalization():
    assert normalize_database_url(
        'postgres://db.example/lessons'
    ) == 'postgresql+psycopg://db.example/lessons'
    assert normalize_database_url(
        'postgresql://db.example/lessons'
    ) == 'postgresql+psycopg://db.example/lessons'
    assert normalize_database_url(
        'postgresql+psycopg://db.example/lessons'
    ) == 'postgresql+psycopg://db.example/lessons'
    assert normalize_database_url(None) is None


def test_homepage_navigation_and_stylesheet(client):
    response = client.get('/')
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'منصة علم الفرائض' in page
    assert 'ابحث عن الدروس وتعلم بسهولة' in page
    assert 'href="/lessons"' in page
    assert 'href="/login"' in page
    assert 'حساب' in page
    assert 'class="search-box"' not in page

    stylesheet = client.get('/static/style.css')
    assert stylesheet.status_code == 200
    assert 'text/css' in stylesheet.content_type


def test_lessons_search_and_category_controls(client):
    response = client.get('/lessons?q=درس&category=faraid')
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'id="lesson-search"' in page
    assert 'id="lesson-category"' in page
    assert 'name="category"' in page


def test_authentication_pages_render_with_shared_navigation(client):
    for path in ('/login', '/register', '/forgot'):
        response = client.get(path)
        assert response.status_code == 200
        assert 'class="site-header"' in response.get_data(as_text=True)
        assert 'static/style.css' in response.get_data(as_text=True)

    with app.app_context():
        email = User.query.filter_by(is_admin=True).first().email
        token = serializer.dumps(email, salt="password-reset-salt")

    reset = client.get(f'/reset/{token}')
    assert reset.status_code == 200
    assert 'name="confirm"' in reset.get_data(as_text=True)


def test_profile_and_student_dashboard_render(client):
    with app.app_context():
        user = User.query.filter_by(is_admin=True).first()
        user_id = user.id
        username = user.username

    with client.session_transaction() as session:
        session['user_id'] = user_id
        session['username'] = username
        session['is_admin'] = True

    dashboard = client.get('/dashboard')
    assert dashboard.status_code == 200
    assert 'الدروس المكتملة' in dashboard.get_data(as_text=True)

    profile = client.get('/profile')
    assert profile.status_code == 200
    assert 'حفظ التغييرات' in profile.get_data(as_text=True)


def test_admin_dashboard_preserves_homepage_and_lesson_forms(client):
    with app.app_context():
        admin_id = User.query.filter_by(is_admin=True).first().id

    with client.session_transaction() as session:
        session['user_id'] = admin_id
        session['is_admin'] = True

    response = client.get('/admin')
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'action="/admin/homepage"' in page
    assert 'action="/admin/add"' in page
    assert 'إعدادات الصفحة الرئيسية' in page
    assert 'إدارة الدروس' in page


def test_lesson_page_uses_shared_layout_and_keeps_navigation(client):
    with app.app_context():
        lesson = Lesson(
            title='UI regression lesson',
            description='وصف توضيحي',
            content='محتوى الدرس',
            video_url='https://youtu.be/ISLAMIC_VIDEO_ID',
        )
        db.session.add(lesson)
        db.session.commit()
        lesson_id = lesson.id
        user_id = User.query.filter_by(is_admin=True).first().id

    with client.session_transaction() as session:
        session['user_id'] = user_id

    response = client.get(f'/lesson/{lesson_id}')
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'class="site-header"' in page
    assert 'العودة إلى الدروس' in page
    assert 'تعليم الدرس كمكتمل' in page
    assert 'src="https://www.youtube.com/embed/ISLAMIC_VIDEO_ID"' in page
    assert 'href="https://youtu.be/ISLAMIC_VIDEO_ID"' in page
    assert 'rel="noopener noreferrer"' in page
