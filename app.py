import flask
from flask import request, session, redirect, url_for, render_template, flash, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = flask.Flask(
    __name__,
    static_folder="static",
    template_folder="templates",
)
app.config["SECRET_KEY"] = os.environ.get("LESSONS_SECRET", "dev-secret-please-change")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'lessons.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# initialize CSRF protection
csrf = CSRFProtect()
csrf.init_app(app)

# make `csrf_token()` available in templates
@app.context_processor
def inject_wtf_csrf():
    return dict(csrf_token=generate_csrf)

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)
    video_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    action = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


def login_required(fn):
    def wrapper(*args, **kwargs):
        if "user_id" not in flask.session:
            return flask.redirect(flask.url_for('login'))
        return fn(*args, **kwargs)

    wrapper.__name__ = fn.__name__
    return wrapper


def create_tables_and_seed():
    # create tables; if schema is outdated (missing columns) recreate DB
    db.create_all()
    inspector = inspect(db.engine)
    # if lesson table exists but lacks 'content' column, recreate schema
    if inspector.has_table('lesson'):
        cols = [c['name'] for c in inspector.get_columns('lesson')]
        if 'content' not in cols:
            # remove file-backed sqlite DB and recreate schema
            try:
                db.drop_all()
            except Exception:
                pass
            db.create_all()
    # seed a sample admin and a few lessons if they don't exist
    if not User.query.filter_by(email='admin@local').first():
        admin = User(
            username='admin',
            email='admin@local',
            password_hash=generate_password_hash('admin123'),
            is_admin=True,
        )
        db.session.add(admin)
        db.session.commit()

    if Lesson.query.count() == 0:
        sample = [
            Lesson(title='درس 1: مقدمة في الفرائض', description='مقدمة حول أساسيات الفرائض', content='محتوى الدرس الأول: شرح المبادئ الأساسية.', video_url='https://www.youtube.com/embed/dQw4w9WgXcQ'),
            Lesson(title='درس 2: الحقوق المتعلقة بالتركة', description='مانقوم به قبل قسمة التركة', content='محتوى الدرس الثاني: قواعد وتقسيمات.', video_url='https://www.youtube.com/embed/dQw4w9WgXcQ'),
            Lesson(title='درس 3: شروط الإرث ', description='دراسة ', content='محتوى الدرس الثالث: أمثلة وحلول عملية.', video_url='https://www.youtube.com/embed/dQw4w9WgXcQ'),
        ]
        db.session.bulk_save_objects(sample)
        db.session.commit()


# serializer for password reset tokens
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])


# ensure DB/tables exist when the module is imported (helps tests and first-run)
with app.app_context():
    create_tables_and_seed()


@app.route('/')
def home():
    lessons = Lesson.query.order_by(Lesson.created_at.desc()).limit(3).all()
    return flask.render_template('index.html', lessons=lessons)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if flask.request.method == 'POST':
        # CSRF is handled by Flask-WTF CSRFProtect (token must be present in form)

        username = flask.request.form.get('username', '').strip()
        email = flask.request.form.get('email', '').strip().lower()
        password = flask.request.form.get('password', '')
        confirm = flask.request.form.get('confirm', '')

        if not username or not email or not password or not confirm:
            flask.flash('الرجاء ملء جميع الحقول', 'error')
            return flask.redirect(flask.url_for('register'))

        if password != confirm:
            flask.flash('كلمتا المرور (password) غير متطابقتين', 'error')
            return flask.redirect(flask.url_for('register'))

        if User.query.filter_by(email=email).first():
            flask.flash( 'البريد الإلكتروني(EMAIL)مستخدم مسبقاً', 'error')
            return flask.redirect(flask.url_for('register'))

        if User.query.filter_by(username=username).first():
            flask.flash('الاسم المستخدم (USERNAME) مستخدم مسبقاً', 'error')
            return flask.redirect(flask.url_for('register'))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        flask.flash('تم إنشاء الحساب بنجاح، يمكنك تسجيل الدخول الآن', 'success')
        return flask.redirect(flask.url_for('login'))

    return flask.render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'POST':
        # CSRF validated by Flask-WTF

        email = flask.request.form.get('email', '').strip().lower()
        password = flask.request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flask.flash('بيانات غير صحيحة', 'error')
            return flask.redirect(flask.url_for('login'))

        flask.session.clear()
        flask.session['user_id'] = user.id
        flask.session['username'] = user.username
        flask.flash('تم تسجيل الدخول', 'success')
        return flask.redirect(flask.url_for('dashboard'))

    return flask.render_template('login.html')


@app.route('/logout')
def logout():
    flask.session.clear()
    return flask.redirect(flask.url_for('home'))


@app.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if flask.request.method == 'POST':
        email = flask.request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user:
            flask.flash('لا يوجد حساب مرتبط بهذا البريد', 'error')
            return flask.redirect(flask.url_for('forgot_password'))

        token = serializer.dumps(user.email, salt='password-reset-salt')
        # For development, show the token/link on screen for testing
        reset_link = flask.url_for('reset_password', token=token, _external=True)
        return flask.render_template('forgot.html', show_token=True, reset_link=reset_link)

    return flask.render_template('forgot.html', show_token=False)


@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600 * 24)
    except SignatureExpired:
        flask.flash('رمز إعادة التعيين قد انتهت صلاحيته', 'error')
        return flask.redirect(flask.url_for('forgot_password'))
    except BadSignature:
        flask.flash('رمز إعادة التعيين غير صالح', 'error')
        return flask.redirect(flask.url_for('forgot_password'))

    user = User.query.filter_by(email=email).first_or_404()
    if flask.request.method == 'POST':
        password = flask.request.form.get('password', '')
        confirm = flask.request.form.get('confirm', '')
        if not password or password != confirm:
            flask.flash('كلمتا المرور غير متطابقتين أو فارغة', 'error')
            return flask.redirect(flask.url_for('reset_password', token=token))

        user.password_hash = generate_password_hash(password)
        db.session.commit()
        flask.flash('تم إعادة تعيين كلمة المرور، يمكنك تسجيل الدخول الآن', 'success')
        return flask.redirect(flask.url_for('login'))

    return flask.render_template('reset.html', token=token)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = db.session.get(User, flask.session.get('user_id'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        if username and username != user.username:
            if User.query.filter_by(username=username).first():
                flash('الاسم المستخدم مستخدم مسبقاً', 'error')
                return redirect(url_for('profile'))
            user.username = username
            session['username'] = username

        if password:
            if password != confirm:
                flash('كلمتا المرور غير متطابقتين', 'error')
                return redirect(url_for('profile'))
            user.password_hash = generate_password_hash(password)

        db.session.commit()
        flash('تم تحديث الملف الشخصي', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)


@app.route('/dashboard')
@login_required
def dashboard():
    user = db.session.get(User, session.get('user_id'))
    q = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    per_page = 6
    lessons_q = Lesson.query.order_by(Lesson.created_at.desc())
    if q:
        lessons_q = lessons_q.filter(Lesson.title.contains(q) | Lesson.description.contains(q) | Lesson.content.contains(q))
    total = lessons_q.count()
    lessons = lessons_q.offset((page-1)*per_page).limit(per_page).all()
    activities = Activity.query.filter_by(user_id=user.id).order_by(Activity.timestamp.desc()).limit(50).all()
    completed = Activity.query.filter_by(user_id=user.id, action='completed_lesson').all()
    completed_count = len({c.lesson_id for c in completed})
    return render_template('dashboard.html', user=user, lessons=lessons, activities=activities, completed_count=completed_count, search_query=q, page=page, per_page=per_page, total=total)


@app.route('/lessons')
def lessons_list():
    q = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    per_page = 6
    lessons_q = Lesson.query.order_by(Lesson.created_at.desc())
    if q:
        lessons_q = lessons_q.filter(Lesson.title.contains(q) | Lesson.description.contains(q) | Lesson.content.contains(q))
    total = lessons_q.count()
    lessons = lessons_q.offset((page-1)*per_page).limit(per_page).all()
    return render_template('lessons.html', lessons=lessons, search_query=q, page=page, per_page=per_page, total=total)


@app.route('/lesson/<int:lesson_id>')
def lesson_detail(lesson_id):
    lesson = db.session.get(Lesson, lesson_id)
    if not lesson:
        abort(404)
    # record anonymous or logged activity
    uid = session.get('user_id')
    if uid:
        act = Activity(user_id=uid, lesson_id=lesson.id, action='viewed_lesson')
        db.session.add(act)
        db.session.commit()

    prev_lesson = Lesson.query.filter(Lesson.id < lesson.id).order_by(Lesson.id.desc()).first()
    next_lesson = Lesson.query.filter(Lesson.id > lesson.id).order_by(Lesson.id.asc()).first()
    return render_template('lesson.html', lesson=lesson, prev_lesson=prev_lesson, next_lesson=next_lesson)


@app.route('/admin')
@login_required
def admin_index():
    user = db.session.get(User, session.get('user_id'))
    if not user.is_admin:
        flash('صلاحيات غير كافية', 'error')
        return redirect(url_for('dashboard'))
    lessons = Lesson.query.order_by(Lesson.created_at.desc()).all()
    activities = Activity.query.order_by(Activity.timestamp.desc()).limit(50).all()
    users = User.query.order_by(User.created_at.desc()).all()
    students_count = len(users)
    lessons_count = Lesson.query.count()
    activity_count = Activity.query.count()
    recent_lessons = Lesson.query.order_by(Lesson.created_at.desc()).limit(5).all()
    return render_template('admin.html', lessons=lessons, activities=activities, users=users, students_count=students_count, lessons_count=lessons_count, activity_count=activity_count, recent_lessons=recent_lessons)


@app.route('/admin/add', methods=['POST'])
@login_required
def admin_add_lesson():
    user = db.session.get(User, session.get('user_id'))
    if not user.is_admin:
        flash('صلاحيات غير كافية', 'error')
        return redirect(url_for('dashboard'))
    # CSRF validated by Flask-WTF

    title = flask.request.form.get('title', '').strip()
    description = flask.request.form.get('description', '').strip()
    content = flask.request.form.get('content', '').strip()
    video_url = flask.request.form.get('video_url', '').strip()
    if not title:
        flask.flash('الرجاء إدخال عنوان الدرس', 'error')
        return flask.redirect(flask.url_for('admin_index'))

    lesson = Lesson(title=title, description=description, content=content, video_url=video_url)
    db.session.add(lesson)
    db.session.commit()
    flash('تم إضافة الدرس', 'success')
    return redirect(url_for('admin_index'))


@app.route('/admin/edit/<int:lesson_id>', methods=['POST'])
@login_required
def admin_edit_lesson(lesson_id):
    user = db.session.get(User, session.get('user_id'))
    if not user.is_admin:
        flash('صلاحيات غير كافية', 'error')
        return redirect(url_for('dashboard'))

    lesson = db.session.get(Lesson, lesson_id)
    if not lesson:
        abort(404)
    # CSRF validated by Flask-WTF

    title = flask.request.form.get('title', '').strip()
    description = flask.request.form.get('description', '').strip()
    content = flask.request.form.get('content', '').strip()
    video_url = flask.request.form.get('video_url', '').strip()

    if not title:
        flask.flash('الرجاء إدخال عنوان الدرس', 'error')
        return flask.redirect(flask.url_for('admin_index'))

    lesson.title = title
    lesson.description = description
    lesson.content = content
    lesson.video_url = video_url
    db.session.commit()
    flask.flash('تم تعديل الدرس', 'success')
    return flask.redirect(flask.url_for('admin_index'))


@app.route('/admin/delete/<int:lesson_id>', methods=['POST'])
@login_required
def admin_delete_lesson(lesson_id):
    user = db.session.get(User, flask.session.get('user_id'))
    if not user.is_admin:
        flask.flash('صلاحيات غير كافية', 'error')
        return flask.redirect(flask.url_for('dashboard'))
    # CSRF validated by Flask-WTF

    lesson = db.session.get(Lesson, lesson_id)
    if not lesson:
        abort(404)
    db.session.delete(lesson)
    db.session.commit()
    flash('تم حذف الدرس', 'success')
    return redirect(url_for('admin_index'))


@app.route('/lesson/complete/<int:lesson_id>', methods=['POST'])
@login_required
def lesson_complete(lesson_id):
    # CSRF validated by Flask-WTF

    lesson = db.session.get(Lesson, lesson_id)
    if not lesson:
        abort(404)
    uid = session.get('user_id')
    if uid:
        act = Activity(user_id=uid, lesson_id=lesson.id, action='completed_lesson')
        db.session.add(act)
        db.session.commit()
        flash('تم تعليم الدرس كمكتمل', 'success')
    return redirect(url_for('lesson_detail', lesson_id=lesson_id))


if __name__ == '__main__':
    # ensure DB/tables exist before first request (Flask 3 removed before_first_request)
    with app.app_context():
        create_tables_and_seed()
if __name__ == '__main__':
    with app.app_context():
        create_tables_and_seed()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=False)