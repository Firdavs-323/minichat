from datetime import datetime

from flask import (
    Flask,
    Response,
    flash,
    get_flashed_messages,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from sqlalchemy import or_

from forms import LoginForm, MessageForm, RegistrationForm, SearchForm
from models import Message, Notification, User, db

app = Flask(__name__)

app.config["SECRET_KEY"] = "maxfiy-kalit-soz-2024"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


SITE_URL = "https://minichat.pythonanywhere.com"
GOOGLE_VERIFICATION_TOKEN = "28o4FvcEoq-aOkqYVOqGLSGuTUKcGDj-nH7rP_cKmtE"
GOOGLE_VERIFICATION_FILE = "google99cf4ddc10057615.html"
DEFAULT_OG_IMAGE = f"{SITE_URL}/static/og-image.svg"
SITEMAP_DATE = "2026-04-02"

GLOBAL_KEYWORDS = [
    "minichat",
    "minichat chat",
    "chat app uzbekistan",
    "online chat python flask",
    "python flask chat app",
    "flask chat project",
    "mini chat web app",
    "online chat uzbekistan",
    "uzbek chat platform",
    "private chat app",
    "secure messaging uzbekistan",
    "contact based chat app",
    "real time chat flask",
    "web chat platform",
    "telegramga o'xshash chat",
    "instagramga o'xshash chat",
    "do'stlar bilan onlayn chat",
    "xabar almashish platformasi",
    "flask social chat project",
    "python web chat",
    "uzbek messenger app",
    "chat website flask",
    "ro'yxatdan o'tib chat qilish",
    "contact management chat",
    "direct message web app",
    "uzbekistan messenger project",
    "messaging website uzbek",
    "web based chat system",
    "lightweight chat application",
    "social chat network uzbekistan",
]

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Iltimos, avval tizimga kiring."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()


def build_seo(
    title,
    description,
    keywords=None,
    canonical=None,
    robots="index, follow",
    image=None,
    schema_type="WebSite",
):
    return {
        "seo_title": title,
        "seo_description": description,
        "seo_keywords": ", ".join(keywords or GLOBAL_KEYWORDS),
        "seo_canonical": canonical or request.url,
        "seo_robots": robots,
        "seo_image": image or DEFAULT_OG_IMAGE,
        "seo_schema_type": schema_type,
    }


@app.context_processor
def inject_defaults():
    return {
        **build_seo(
            title="minichat - Flask asosidagi mini chat platformasi",
            description=(
                "minichat - foydalanuvchilar account yaratib, do'stlarini kontaktga qo'shib, "
                "ular bilan onlayn chat qila oladigan o'zbekcha mini chat web ilova."
            ),
            canonical=request.url,
        ),
        "site_url": SITE_URL,
        "google_verification_token": GOOGLE_VERIFICATION_TOKEN,
    }


@app.route("/")
def index():
    return render_template(
        "index.html",
        **build_seo(
            title="minichat - O'zbekcha mini chat va online muloqot platformasi",
            description=(
                "minichat - Flask backend asosida qurilgan mini chat ilova. "
                "Account yarating, do'stlaringizni kontaktga qo'shing va ular bilan "
                "xavfsiz onlayn muloqot qiling."
            ),
            keywords=GLOBAL_KEYWORDS
            + [
                "minichat pythonanywhere",
                "chat app uzbek",
                "online chat sayt",
                "friend messaging app",
                "simple messenger web app",
            ],
            canonical=f"{SITE_URL}/",
            schema_type="SoftwareApplication",
        ),
    )

@app.route('/robots.txt')
def robots():
    return app.send_static_file('robots.txt')

from flask import Response

@app.route("/sitemap.xml")
def sitemap():
    pages = []

    pages.append("https://minichat.pythonanywhere.com/")
    pages.append("https://minichat.pythonanywhere.com/login")
    pages.append("https://minichat.pythonanywhere.com/register")

    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap_xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for page in pages:
        sitemap_xml.append(f"""
        <url>
            <loc>{page}</loc>
        </url>
        """)

    sitemap_xml.append('</urlset>')

    return Response("\n".join(sitemap_xml), mimetype='application/xml')

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("Ro'yxatdan muvaffaqiyatli o'tdingiz! Endi tizimga kirishingiz mumkin.", "success")
        return redirect(url_for("login"))

    return render_template(
        "register.html",
        form=form,
        **build_seo(
            title="Ro'yxatdan o'tish - minichat chat account yaratish",
            description=(
                "minichat mini chat ilovasida yangi profil yarating, account oching va "
                "do'stlaringiz bilan chat qilishni boshlang."
            ),
            keywords=GLOBAL_KEYWORDS + ["minichat register", "chat signup", "messenger account yaratish"],
            canonical=f"{SITE_URL}/register",
        ),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            user.is_online = True
            user.last_seen = datetime.now()
            db.session.commit()

            flash(f"Xush kelibsiz, {user.username}!", "success")
            return redirect(url_for("dashboard"))

        flash("Username yoki parol noto'g'ri.", "danger")

    return render_template(
        "login.html",
        form=form,
        **build_seo(
            title="Kirish - minichat account login sahifasi",
            description=(
                "minichat accountiga kiring va kontaktlaringiz bilan xabar almashishni davom ettiring."
            ),
            keywords=GLOBAL_KEYWORDS + ["minichat login", "chat login", "messenger sign in"],
            canonical=f"{SITE_URL}/login",
        ),
    )


@app.route("/logout")
@login_required
def logout():
    current_user.is_online = False
    current_user.last_seen = datetime.now()
    db.session.commit()
    logout_user()
    flash("Tizimdan chiqdingiz.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    recent_messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).order_by(Message.timestamp.desc()).limit(10).all()
    contacts = current_user.get_contacts()
    unread_count = current_user.get_unread_messages_count()

    return render_template(
        "dashboard.html",
        recent_messages=recent_messages,
        contacts=contacts,
        unread_count=unread_count,
        **build_seo(
            title="Dashboard - minichat",
            description="minichat foydalanuvchi boshqaruv paneli.",
            keywords=["minichat dashboard", "chat dashboard", "user panel"],
            canonical=f"{SITE_URL}/dashboard",
            robots="noindex, nofollow",
        ),
    )


@app.route("/search_users", methods=["GET", "POST"])
@login_required
def search_users():
    form = SearchForm()
    search_query = request.values.get("search", "").strip()
    users = []

    if request.method == "POST" and form.validate_on_submit():
        search_query = form.search.data.strip()

    if request.method == "GET" and search_query:
        form.search.data = search_query

    if search_query:
        users = User.query.filter(
            User.id != current_user.id,
            or_(
                User.username.contains(search_query),
                User.first_name.contains(search_query),
                User.last_name.contains(search_query),
                User.email.contains(search_query),
            ),
        ).limit(20).all()

    return render_template(
        "search_users.html",
        form=form,
        users=users,
        search_query=search_query,
        **build_seo(
            title="Foydalanuvchi qidirish - minichat",
            description="minichat ichida do'stlaringizni ism, username yoki email bo'yicha qidiring.",
            keywords=["minichat search", "find friends", "contact search", "user lookup"],
            canonical=f"{SITE_URL}/search_users",
            robots="noindex, nofollow",
        ),
    )


@app.route("/add_contact/<int:user_id>")
@login_required
def add_contact(user_id):
    user = User.query.get_or_404(user_id)

    if user == current_user:
        flash("O'zingizni kontaktga qo'sha olmaysiz.", "warning")
        return redirect(url_for("search_users"))

    if current_user.add_contact(user):
        db.session.commit()
        flash(f"{user.username} kontaktlarga qo'shildi.", "success")
    else:
        flash(f"{user.username} allaqachon kontaktlaringizda.", "info")

    return redirect(url_for("contacts"))


@app.route("/remove_contact/<int:user_id>")
@login_required
def remove_contact(user_id):
    user = User.query.get_or_404(user_id)

    if current_user.remove_contact(user):
        db.session.commit()
        flash(f"{user.username} kontaktlardan o'chirildi.", "success")
    else:
        flash("Xatolik yuz berdi.", "danger")

    return redirect(url_for("contacts"))


@app.route("/contacts")
@login_required
def contacts():
    try:
        contacts_list = current_user.get_contacts()
        return render_template(
            "contacts.html",
            contacts=contacts_list,
            **build_seo(
                title="Kontaktlar - minichat",
                description="minichat kontaktlar ro'yxati sahifasi.",
                keywords=["minichat contacts", "friend list", "chat contacts"],
                canonical=f"{SITE_URL}/contacts",
                robots="noindex, nofollow",
            ),
        )
    except Exception as exc:
        print(f"Xatolik: {exc}")
        flash("Kontaktlarni yuklashda xatolik yuz berdi", "danger")
        return render_template(
            "contacts.html",
            contacts=[],
            **build_seo(
                title="Kontaktlar - minichat",
                description="minichat kontaktlar ro'yxati sahifasi.",
                keywords=["minichat contacts", "friend list", "chat contacts"],
                canonical=f"{SITE_URL}/contacts",
                robots="noindex, nofollow",
            ),
        )


@app.route("/chat/<int:user_id>", methods=["GET", "POST"])
@login_required
def chat(user_id):
    other_user = User.query.get_or_404(user_id)

    if not current_user.is_contact(other_user) and other_user != current_user:
        flash("Faqat kontaktlaringiz bilan chat qilishingiz mumkin.", "warning")
        return redirect(url_for("contacts"))

    form = MessageForm()

    if form.validate_on_submit():
        new_message = Message(
            sender_id=current_user.id,
            receiver_id=other_user.id,
            content=form.content.data,
        )
        db.session.add(new_message)
        db.session.commit()

        notification = Notification(
            user_id=other_user.id,
            message=f"{current_user.username} sizga yangi xabar yubordi",
            type="message",
            link=url_for("chat", user_id=current_user.id, _external=True),
        )
        db.session.add(notification)
        db.session.commit()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": True})

        return redirect(url_for("chat", user_id=user_id))

    if form.errors and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        errors = "; ".join(error for field_errors in form.errors.values() for error in field_errors)
        return jsonify({"success": False, "error": errors})

    unread_messages = Message.query.filter_by(
        sender_id=other_user.id,
        receiver_id=current_user.id,
        is_read=False,
    ).all()

    for message in unread_messages:
        message.is_read = True

    db.session.commit()

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other_user.id))
        | ((Message.sender_id == other_user.id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp).all()

    flashed_messages = get_flashed_messages(with_categories=True)
    return render_template(
        "chat.html",
        form=form,
        messages=messages,
        other_user=other_user,
        flashed_messages=flashed_messages,
        **build_seo(
            title=f"Chat - {other_user.username} | minichat",
            description="minichat shaxsiy chat sahifasi.",
            keywords=["private chat", "direct message", "minichat chat"],
            canonical=f"{SITE_URL}/chat/{user_id}",
            robots="noindex, nofollow",
        ),
    )


@app.route("/get_notifications")
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False,
    ).order_by(Notification.created_at.desc()).all()

    return jsonify(
        [
            {
                "id": item.id,
                "message": item.message,
                "type": item.type,
                "link": item.link,
                "created_at": item.created_at.strftime("%H:%M"),
            }
            for item in notifications
        ]
    )


@app.route("/mark_notification_read/<int:notification_id>")
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)

    if notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()

    return redirect(notification.link or url_for("dashboard"))


@app.route("/api/check_new_messages/<int:user_id>")
@login_required
def check_new_messages(user_id):
    new_count = Message.query.filter(
        Message.sender_id == user_id,
        Message.receiver_id == current_user.id,
        Message.is_read.is_(False),
    ).count()
    return jsonify({"new_count": new_count})


@app.route("/robots.txt")
def robots():
    body = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /dashboard",
            "Disallow: /contacts",
            "Disallow: /chat/",
            "Disallow: /search_users",
            f"Sitemap: {SITE_URL}/sitemap.xml",
        ]
    )
    return Response(body, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    pages = [
        ("index", "daily", "1.0"),
        ("register", "weekly", "0.8"),
        ("login", "monthly", "0.6"),
    ]

    urls = []
    for endpoint, changefreq, priority in pages:
        urls.append(
            f"""
    <url>
        <loc>{url_for(endpoint, _external=True)}</loc>
        <lastmod>{SITEMAP_DATE}</lastmod>
        <changefreq>{changefreq}</changefreq>
        <priority>{priority}</priority>
    </url>"""
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{''.join(urls)}\n"
        "</urlset>"
    )
    return Response(xml, mimetype="application/xml")


@app.route(f"/{GOOGLE_VERIFICATION_FILE}")
def google_verification_file():
    return Response(
        f"google-site-verification: {GOOGLE_VERIFICATION_FILE}",
        mimetype="text/html",
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
