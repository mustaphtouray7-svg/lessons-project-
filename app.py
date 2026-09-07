import flask
from flask import request, session, redirect, url_for, render_template, flash, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text, func
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from functools import wraps


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


app = flask.Flask(
    __name__,
    static_folder="static",
    template_folder="templates",
)

app.config["SECRET_KEY"] = os.environ.get(
    "LESSONS_SECRET",
    "dev-secret-please-change"
)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{os.path.join(BASE_DIR, 'lessons.db')}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# ---------------------------------------------------------
# CSRF PROTECTION
# ---------------------------------------------------------

csrf = CSRFProtect()
csrf.init_app(app)


@app.context_processor
def inject_wtf_csrf():
    return dict(csrf_token=generate_csrf)


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

db = SQLAlchemy(app)


# ---------------------------------------------------------
# USER MODEL
# ---------------------------------------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    email = db.Column(
        db.String(200),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(200),
        nullable=False
    )

    is_admin = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )


# ---------------------------------------------------------
# LESSON MODEL
# ---------------------------------------------------------

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(250),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    content = db.Column(
        db.Text,
        nullable=True
    )

    video_url = db.Column(
        db.String(500),
        nullable=True
    )

    category = db.Column(
        db.String(50),
        nullable=False,
        default="faraid"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ---------------------------------------------------------
# ACTIVITY MODEL
# ---------------------------------------------------------

class Activity(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    lesson_id = db.Column(
        db.Integer,
        db.ForeignKey("lesson.id"),
        nullable=True
    )

    action = db.Column(
        db.String(100),
        nullable=False
    )

    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ---------------------------------------------------------
# HOMEPAGE SETTINGS
# ---------------------------------------------------------

class HomepageSettings(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(250),
        nullable=False,
        default="منصة علم الفرائض"
    )

    description = db.Column(
        db.Text,
        nullable=True,
        default="تعلّم بطريقة منظمة"
    )

    image_url = db.Column(
        db.String(500),
        nullable=True,
        default=""
    )

    button_text = db.Column(
        db.String(150),
        nullable=False,
        default="استكشف الدروس"
    )


# ---------------------------------------------------------
# LOGIN PROTECTION
# ---------------------------------------------------------

def login_required(fn):

    @wraps(fn)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):

    @wraps(fn)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        user = db.session.get(
            User,
            session.get("user_id")
        )

        if not user or not user.is_admin:
            flash("صلاحيات غير كافية", "error")
            return redirect(url_for("dashboard"))

        return fn(*args, **kwargs)

    return wrapper


# ---------------------------------------------------------
# CATEGORY HELPERS
# ---------------------------------------------------------

CATEGORY_NAMES = {
    "faraid": "الفرائض",
    "nahw": "النحو",
    "fiqh": "الفقه",
}


def normalize_category(category):

    category = (category or "faraid").strip().lower()

    if category not in CATEGORY_NAMES:
        return "faraid"

    return category


# ---------------------------------------------------------
# DATABASE SETUP AND SAFE MIGRATION
# ---------------------------------------------------------

def create_tables_and_seed():

    db.create_all()

    inspector = inspect(db.engine)

    # -----------------------------------------------------
    # Safely add category column if an older database
    # does not have it.
    # -----------------------------------------------------

    if inspector.has_table("lesson"):

        columns = [
            column["name"]
            for column in inspector.get_columns("lesson")
        ]

        if "category" not in columns:

            with db.engine.begin() as connection:

                connection.execute(
                    text(
                        "ALTER TABLE lesson "
                        "ADD COLUMN category VARCHAR(50) "
                        "DEFAULT 'faraid'"
                    )
                )

    # -----------------------------------------------------
    # Make sure homepage settings exist.
    # -----------------------------------------------------

    homepage = HomepageSettings.query.first()

    if not homepage:

        homepage = HomepageSettings(
            title="منصة علم الفرائض",
            description="تعلّم بطريقة منظمة",
            image_url="",
            button_text="استكشف الدروس",
        )

        db.session.add(homepage)
        db.session.commit()

    # -----------------------------------------------------
    # ADMIN ACCOUNT
    #
    # Username: Kelay336
    # Email: Mustaphtouray7@gmail.com
    # Password: gambia2026
    #
    # Existing admin account is updated instead of creating
    # unnecessary duplicate admin accounts.
    # -----------------------------------------------------

    admin_email = "Mustaphtouray7@gmail.com"
    admin_username = "Kelay336"
    admin_password = "gambia2026"

    admin = User.query.filter_by(
        email=admin_email
    ).first()

    if not admin:

        # Look for an existing administrator.
        admin = User.query.filter_by(
            is_admin=True
        ).first()

    if admin:

        # Update the existing admin account.
        admin.username = admin_username
        admin.email = admin_email
        admin.is_admin = True

        # Keep the requested admin password.
        admin.password_hash = generate_password_hash(
            admin_password
        )

    else:

        admin = User(
            username=admin_username,
            email=admin_email,
            password_hash=generate_password_hash(
                admin_password
            ),
            is_admin=True,
        )

        db.session.add(admin)

    db.session.commit()


    if Lesson.query.count() == 0:

        sample = [

            Lesson(
                title="درس 1: مقدمة في الفرائض",
                description="مقدمة حول أساسيات الفرائض",
                content="محتوى الدرس الأول: شرح المبادئ الأساسية.",
                video_url="",
                category="faraid",
            ),

            Lesson(
                title="درس 2: الحقوق المتعلقة بالتركة",
                description="ما نقوم به قبل قسمة التركة",
                content="محتوى الدرس الثاني: قواعد وتقسيمات.",
                video_url="",
                category="faraid",
            ),

            Lesson(
                title="درس 3: شروط الإرث",
                description="دراسة",
                content="محتوى الدرس الثالث: أمثلة وحلول عملية.",
                video_url="",
                category="faraid",
            ),
        ]

        db.session.add_all(sample)
        db.session.commit()


# ---------------------------------------------------------
# PASSWORD RESET SERIALIZER
# ---------------------------------------------------------

serializer = URLSafeTimedSerializer(
    app.config["SECRET_KEY"]
)


# ---------------------------------------------------------
# INITIAL DATABASE SETUP
# ---------------------------------------------------------

with app.app_context():
    create_tables_and_seed()


# ---------------------------------------------------------
# HOMEPAGE
# ---------------------------------------------------------

@app.route("/")
def home():

    homepage = HomepageSettings.query.first()

    if not homepage:

        homepage = HomepageSettings(
            title="منصة علم الفرائض",
            description="تعلّم بطريقة منظمة",
            image_url="",
            button_text="استكشف الدروس",
        )

    lessons = (
        Lesson.query
        .order_by(Lesson.created_at.desc())
        .limit(3)
        .all()
    )

    categories = CATEGORY_NAMES

    return render_template(
        "index.html",
        lessons=lessons,
        homepage=homepage,
        categories=categories,
    )


# ---------------------------------------------------------
# CATEGORY PAGE
# ---------------------------------------------------------

@app.route("/category/<category>")
def category_lessons(category):

    category = normalize_category(category)

    lessons = (
        Lesson.query
        .filter_by(category=category)
        .order_by(Lesson.created_at.desc())
        .all()
    )

    return render_template(
        "lessons.html",
        lessons=lessons,
        search_query="",
        page=1,
        per_page=len(lessons) if lessons else 1,
        total=len(lessons),
        category=category,
        category_name=CATEGORY_NAMES[category],
    )


# ---------------------------------------------------------
# REGISTER
# ---------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm = request.form.get(
            "confirm",
            ""
        )

        if not username or not email or not password or not confirm:

            flash(
                "الرجاء ملء جميع الحقول",
                "error"
            )

            return redirect(
                url_for("register")
            )

        if password != confirm:

            flash(
                "كلمتا المرور غير متطابقتين",
                "error"
            )

            return redirect(
                url_for("register")
            )

        if User.query.filter_by(
            email=email
        ).first():

            flash(
                "البريد الإلكتروني مستخدم مسبقاً",
                "error"
            )

            return redirect(
                url_for("register")
            )

        if User.query.filter_by(
            username=username
        ).first():

            flash(
                "اسم المستخدم مستخدم مسبقاً",
                "error"
            )

            return redirect(
                url_for("register")
            )

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(
                password
            ),
        )

        db.session.add(user)
        db.session.commit()

        flash(
            "تم إنشاء الحساب بنجاح، يمكنك تسجيل الدخول الآن",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter(
    func.lower(User.email) == email
).first()
        if not user or not user.check_password(password):

            flash(
                "بيانات تسجيل الدخول غير صحيحة",
                "error"
            )

            return redirect(
                url_for("login")
            )

        session.clear()

        session["user_id"] = user.id
        session["username"] = user.username
        session["is_admin"] = bool(user.is_admin)

        flash(
            "تم تسجيل الدخول بنجاح",
            "success"
        )

        if user.is_admin:
            return redirect(
                url_for("admin_index")
            )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "login.html"
    )


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# ---------------------------------------------------------
# FORGOT PASSWORD
# ---------------------------------------------------------

@app.route("/forgot", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        user = User.query.filter_by(
            email=email
        ).first()

        if not user:

            flash(
                "لا يوجد حساب مرتبط بهذا البريد",
                "error"
            )

            return redirect(
                url_for("forgot_password")
            )

        token = serializer.dumps(
            user.email,
            salt="password-reset-salt"
        )

        reset_link = url_for(
            "reset_password",
            token=token,
            _external=True
        )

        return render_template(
            "forgot.html",
            show_token=True,
            reset_link=reset_link,
        )

    return render_template(
        "forgot.html",
        show_token=False
    )


# ---------------------------------------------------------
# RESET PASSWORD
# ---------------------------------------------------------

@app.route(
    "/reset/<token>",
    methods=["GET", "POST"]
)
def reset_password(token):

    try:

        email = serializer.loads(
            token,
            salt="password-reset-salt",
            max_age=3600 * 24
        )

    except SignatureExpired:

        flash(
            "رمز إعادة التعيين قد انتهت صلاحيته",
            "error"
        )

        return redirect(
            url_for("forgot_password")
        )

    except BadSignature:

        flash(
            "رمز إعادة التعيين غير صالح",
            "error"
        )

        return redirect(
            url_for("forgot_password")
        )

    user = User.query.filter_by(
        email=email
    ).first_or_404()

    if request.method == "POST":

        password = request.form.get(
            "password",
            ""
        )

        confirm = request.form.get(
            "confirm",
            ""
        )

        if not password or password != confirm:

            flash(
                "كلمتا المرور غير متطابقتين أو فارغة",
                "error"
            )

            return redirect(
                url_for(
                    "reset_password",
                    token=token
                )
            )

        user.password_hash = generate_password_hash(
            password
        )

        db.session.commit()

        flash(
            "تم إعادة تعيين كلمة المرور، يمكنك تسجيل الدخول الآن",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "reset.html",
        token=token
    )


# ---------------------------------------------------------
# PROFILE
# ---------------------------------------------------------

@app.route(
    "/profile",
    methods=["GET", "POST"]
)
@login_required
def profile():

    user = db.session.get(
        User,
        session.get("user_id")
    )

    if not user:
        session.clear()
        return redirect(url_for("login"))

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm = request.form.get(
            "confirm",
            ""
        )

        if username and username != user.username:

            existing = User.query.filter_by(
                username=username
            ).first()

            if existing:

                flash(
                    "اسم المستخدم مستخدم مسبقاً",
                    "error"
                )

                return redirect(
                    url_for("profile")
                )

            user.username = username
            session["username"] = username

        if password:

            if password != confirm:

                flash(
                    "كلمتا المرور غير متطابقتين",
                    "error"
                )

                return redirect(
                    url_for("profile")
                )

            user.password_hash = generate_password_hash(
                password
            )

        db.session.commit()

        flash(
            "تم تحديث الملف الشخصي",
            "success"
        )

        return redirect(
            url_for("profile")
        )

    return render_template(
        "profile.html",
        user=user
    )


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    user = db.session.get(
        User,
        session.get("user_id")
    )

    if not user:
        session.clear()
        return redirect(url_for("login"))

    q = request.args.get(
        "q",
        ""
    ).strip()

    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except ValueError:
        page = 1

    per_page = 6

    lessons_q = Lesson.query.order_by(
        Lesson.created_at.desc()
    )

    if q:

        search_term = f"%{q}%"

        lessons_q = lessons_q.filter(
            db.or_(
                Lesson.title.ilike(search_term),
                Lesson.description.ilike(search_term),
                Lesson.content.ilike(search_term)
            )
        )

    total = lessons_q.count()

    lessons = (
        lessons_q
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    activities = (
        Activity.query
        .filter_by(user_id=user.id)
        .order_by(Activity.timestamp.desc())
        .limit(50)
        .all()
    )

    completed = (
        Activity.query
        .filter_by(
            user_id=user.id,
            action="completed_lesson"
        )
        .all()
    )

    completed_count = len(
        {
            activity.lesson_id
            for activity in completed
            if activity.lesson_id
        }
    )

    return render_template(
        "dashboard.html",
        user=user,
        lessons=lessons,
        activities=activities,
        completed_count=completed_count,
        search_query=q,
        page=page,
        per_page=per_page,
        total=total,
    )


# ---------------------------------------------------------
# LESSONS LIST
# ---------------------------------------------------------

@app.route("/lessons")
def lessons_list():

    q = request.args.get(
        "q",
        ""
    ).strip()

    category = request.args.get(
        "category",
        ""
    ).strip().lower()

    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except ValueError:
        page = 1

    per_page = 6

    lessons_q = Lesson.query.order_by(
        Lesson.created_at.desc()
    )

    if category in CATEGORY_NAMES:

        lessons_q = lessons_q.filter_by(
            category=category
        )

    if q:

        search_term = f"%{q}%"

        lessons_q = lessons_q.filter(
            db.or_(
                Lesson.title.ilike(search_term),
                Lesson.description.ilike(search_term),
                Lesson.content.ilike(search_term)
            )
        )

    total = lessons_q.count()

    lessons = (
        lessons_q
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return render_template(
        "lessons.html",
        lessons=lessons,
        search_query=q,
        page=page,
        per_page=per_page,
        total=total,
        category=category,
        category_name=CATEGORY_NAMES.get(
            category,
            ""
        ),
    )


# ---------------------------------------------------------
# LESSON DETAILS
# ---------------------------------------------------------

@app.route(
    "/lesson/<int:lesson_id>"
)
def lesson_detail(lesson_id):

    lesson = db.session.get(
        Lesson,
        lesson_id
    )

    if not lesson:
        abort(404)

    uid = session.get(
        "user_id"
    )

    if uid:

        activity = Activity(
            user_id=uid,
            lesson_id=lesson.id,
            action="viewed_lesson"
        )

        db.session.add(activity)
        db.session.commit()

    previous_lesson = (
        Lesson.query
        .filter(
            Lesson.id < lesson.id
        )
        .order_by(
            Lesson.id.desc()
        )
        .first()
    )

    next_lesson = (
        Lesson.query
        .filter(
            Lesson.id > lesson.id
        )
        .order_by(
            Lesson.id.asc()
        )
        .first()
    )

    return render_template(
        "lesson.html",
        lesson=lesson,
        prev_lesson=previous_lesson,
        next_lesson=next_lesson,
    )


# ---------------------------------------------------------
# ADMIN DASHBOARD
# ---------------------------------------------------------

@app.route("/admin")
@admin_required
def admin_index():

    lessons = (
        Lesson.query
        .order_by(Lesson.created_at.desc())
        .all()
    )

    activities = (
        Activity.query
        .order_by(Activity.timestamp.desc())
        .limit(50)
        .all()
    )

    users = (
        User.query
        .order_by(User.created_at.desc())
        .all()
    )

    students_count = User.query.filter_by(
        is_admin=False
    ).count()

    lessons_count = Lesson.query.count()

    activity_count = Activity.query.count()

    recent_lessons = (
        Lesson.query
        .order_by(Lesson.created_at.desc())
        .limit(5)
        .all()
    )

    homepage = HomepageSettings.query.first()

    return render_template(
        "admin.html",
        lessons=lessons,
        activities=activities,
        users=users,
        students_count=students_count,
        lessons_count=lessons_count,
        activity_count=activity_count,
        recent_lessons=recent_lessons,
        homepage=homepage,
        categories=CATEGORY_NAMES,
    )


# ---------------------------------------------------------
# ADMIN ADD LESSON
# ---------------------------------------------------------

@app.route(
    "/admin/add",
    methods=["POST"]
)
@admin_required
def admin_add_lesson():

    title = request.form.get(
        "title",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    content = request.form.get(
        "content",
        ""
    ).strip()

    video_url = request.form.get(
        "video_url",
        ""
    ).strip()

    category = normalize_category(
        request.form.get(
            "category",
            "faraid"
        )
    )

    if not title:

        flash(
            "الرجاء إدخال عنوان الدرس",
            "error"
        )

        return redirect(
            url_for("admin_index")
        )

    lesson = Lesson(
        title=title,
        description=description,
        content=content,
        video_url=video_url,
        category=category,
    )

    db.session.add(lesson)
    db.session.commit()

    flash(
        "تم إضافة الدرس بنجاح",
        "success"
    )

    return redirect(
        url_for("admin_index")
    )


# ---------------------------------------------------------
# ADMIN EDIT LESSON
# ---------------------------------------------------------

@app.route(
    "/admin/edit/<int:lesson_id>",
    methods=["POST"]
)
@admin_required
def admin_edit_lesson(lesson_id):

    lesson = db.session.get(
        Lesson,
        lesson_id
    )

    if not lesson:
        abort(404)

    title = request.form.get(
        "title",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    content = request.form.get(
        "content",
        ""
    ).strip()

    video_url = request.form.get(
        "video_url",
        ""
    ).strip()

    category = normalize_category(
        request.form.get(
            "category",
            lesson.category or "faraid"
        )
    )

    if not title:

        flash(
            "الرجاء إدخال عنوان الدرس",
            "error"
        )

        return redirect(
            url_for("admin_index")
        )

    lesson.title = title
    lesson.description = description
    lesson.content = content
    lesson.video_url = video_url
    lesson.category = category

    db.session.commit()

    flash(
        "تم تعديل الدرس بنجاح",
        "success"
    )

    return redirect(
        url_for("admin_index")
    )


# ---------------------------------------------------------
# ADMIN DELETE LESSON
# ---------------------------------------------------------

@app.route(
    "/admin/delete/<int:lesson_id>",
    methods=["POST"]
)
@admin_required
def admin_delete_lesson(lesson_id):

    lesson = db.session.get(
        Lesson,
        lesson_id
    )

    if not lesson:
        abort(404)

    # Delete related activities first.
    Activity.query.filter_by(
        lesson_id=lesson.id
    ).delete(
        synchronize_session=False
    )

    db.session.delete(lesson)
    db.session.commit()

    flash(
        "تم حذف الدرس",
        "success"
    )

    return redirect(
        url_for("admin_index")
    )


# ---------------------------------------------------------
# ADMIN HOMEPAGE EDITOR
# ---------------------------------------------------------

@app.route(
    "/admin/homepage",
    methods=["POST"]
)
@admin_required
def admin_edit_homepage():

    homepage = HomepageSettings.query.first()

    if not homepage:

        homepage = HomepageSettings()
        db.session.add(homepage)

    title = request.form.get(
        "title",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    image_url = request.form.get(
        "image_url",
        ""
    ).strip()

    button_text = request.form.get(
        "button_text",
        ""
    ).strip()

    if title:
        homepage.title = title

    homepage.description = description
    homepage.image_url = image_url

    if button_text:
        homepage.button_text = button_text

    db.session.commit()

    flash(
        "تم تحديث الصفحة الرئيسية بنجاح",
        "success"
    )

    return redirect(
        url_for("admin_index")
    )


# ---------------------------------------------------------
# MARK LESSON COMPLETE
# ---------------------------------------------------------

@app.route(
    "/lesson/complete/<int:lesson_id>",
    methods=["POST"]
)
@login_required
def lesson_complete(lesson_id):

    lesson = db.session.get(
        Lesson,
        lesson_id
    )

    if not lesson:
        abort(404)

    uid = session.get(
        "user_id"
    )

    if uid:

        activity = Activity(
            user_id=uid,
            lesson_id=lesson.id,
            action="completed_lesson"
        )

        db.session.add(activity)
        db.session.commit()

        flash(
            "تم تعليم الدرس كمكتمل",
            "success"
        )

    return redirect(
        url_for(
            "lesson_detail",
            lesson_id=lesson_id
        )
    )


# ---------------------------------------------------------
# APPLICATION START
# ---------------------------------------------------------

if __name__ == "__main__":

    with app.app_context():
        create_tables_and_seed()

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                10000
            )
        ),
        debug=False
    )