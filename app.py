from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, get_flashed_messages
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Message, Notification
from forms import RegistrationForm, LoginForm, SearchForm, MessageForm
from datetime import datetime
from sqlalchemy import or_

app = Flask(__name__)

# Konfiguratsiya
app.config['SECRET_KEY'] = 'maxfiy-kalit-soz-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ma'lumotlar bazasini ishga tushirish
db.init_app(app)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Iltimos, avval tizimga kiring.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Ma'lumotlar bazasini yaratish
with app.app_context():
    db.create_all()
    print("Ma'lumotlar bazasi yaratildi!")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Ro\'yxatdan muvaffaqiyatli o\'tdingiz! Endi tizimga kirishingiz mumkin.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user)
            user.is_online = True
            user.last_seen = datetime.now()
            db.session.commit()
            
            flash(f'Xush kelibsiz, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Username yoki parol noto\'g\'ri.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    current_user.is_online = False
    current_user.last_seen = datetime.now()
    db.session.commit()
    logout_user()
    flash('Tizimdan chiqdingiz.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Oxirgi xabarlar
    recent_messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).order_by(Message.timestamp.desc()).limit(10).all()
    
    # Kontaktlar
    contacts = current_user.get_contacts()
    
    # O'qilmagan xabarlar soni
    unread_count = current_user.get_unread_messages_count()
    
    return render_template('dashboard.html', 
                         recent_messages=recent_messages,
                         contacts=contacts,
                         unread_count=unread_count)

@app.route('/search_users', methods=['GET', 'POST'])
@login_required
def search_users():
    form = SearchForm()
    users = []
    
    if form.validate_on_submit():
        search_query = form.search.data
        users = User.query.filter(
            User.id != current_user.id,
            or_(
                User.username.contains(search_query),
                User.first_name.contains(search_query),
                User.last_name.contains(search_query),
                User.email.contains(search_query)
            )
        ).limit(20).all()
    
    return render_template('search_users.html', form=form, users=users)

@app.route('/add_contact/<int:user_id>')
@login_required
def add_contact(user_id):
    user = User.query.get_or_404(user_id)
    
    if user == current_user:
        flash('O\'zingizni kontaktga qo\'sha olmaysiz.', 'warning')
        return redirect(url_for('search_users'))
    
    if current_user.add_contact(user):
        db.session.commit()
        flash(f'{user.username} kontaktlarga qo\'shildi.', 'success')
    else:
        flash(f'{user.username} allaqachon kontaktlaringizda.', 'info')
    
    return redirect(url_for('contacts'))

@app.route('/remove_contact/<int:user_id>')
@login_required
def remove_contact(user_id):
    user = User.query.get_or_404(user_id)
    
    if current_user.remove_contact(user):
        db.session.commit()
        flash(f'{user.username} kontaktlardan o\'chirildi.', 'success')
    else:
        flash('Xatolik yuz berdi.', 'danger')
    
    return redirect(url_for('contacts'))

# KONTAKT ROUTE - FAQAT 1 MARTA!
@app.route('/contacts')
@login_required
def contacts():
    """Kontaktlar ro'yxati"""
    try:
        contacts_list = current_user.get_contacts()
        return render_template('contacts.html', contacts=contacts_list)
    except Exception as e:
        print(f"Xatolik: {e}")
        flash("Kontaktlarni yuklashda xatolik yuz berdi", 'danger')
        return render_template('contacts.html', contacts=[])

@app.route('/chat/<int:user_id>', methods=['GET', 'POST'])
@login_required
def chat(user_id):
    other_user = User.query.get_or_404(user_id)
    
    # Faqat kontaktlar bilan chatlashish mumkin
    if not current_user.is_contact(other_user) and other_user != current_user:
        flash('Faqat kontaktlaringiz bilan chat qilishingiz mumkin.', 'warning')
        return redirect(url_for('contacts'))
    
    form = MessageForm()
    
    if form.validate_on_submit():
        message = Message(
            sender_id=current_user.id,
            receiver_id=other_user.id,
            content=form.content.data
        )
        db.session.add(message)
        db.session.commit()
        
        # Bildirishnoma yaratish
        notification = Notification(
            user_id=other_user.id,
            message=f"{current_user.username} sizga yangi xabar yubordi",
            type='message',
            link=url_for('chat', user_id=current_user.id, _external=True)
        )
        db.session.add(notification)
        db.session.commit()
        
        # AJAX uchun JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})
        
        return redirect(url_for('chat', user_id=user_id))
    
    else:
        # Form validation error
        errors = '; '.join([error for field in form.errors for error in field])
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': errors})
    
    # Xabarlarni o'qilgan deb belgilash
    unread_messages = Message.query.filter_by(
        sender_id=other_user.id,
        receiver_id=current_user.id,
        is_read=False
    ).all()

    
    for message in unread_messages:
        message.is_read = True
    
    db.session.commit()
    
    # Xabarlarni olish
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other_user.id)) |
        ((Message.sender_id == other_user.id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp).all()
    
    flashed_messages = get_flashed_messages(with_categories=True)
    return render_template('chat.html', 
                         form=form, 
                         messages=messages, 
                         other_user=other_user,
                         flashed_messages=flashed_messages)


@app.route('/get_notifications')
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).all()
    
    return jsonify([{
        'id': n.id,
        'message': n.message,
        'type': n.type,
        'link': n.link,
        'created_at': n.created_at.strftime('%H:%M')
    } for n in notifications])

@app.route('/mark_notification_read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
    
    return redirect(notification.link or url_for('dashboard'))

# API endpoint for checking new messages (for AJAX)
from flask import jsonify
from flask_login import login_required, current_user

@app.route("/api/check_new_messages/<int:user_id>")
@login_required
def check_new_messages(user_id):
    # O'qilmagan xabarlar soni
    new_count = Message.query.filter(
        Message.sender_id == user_id,
        Message.receiver_id == current_user.id,
        Message.is_read == False
    ).count()
    
    return jsonify({
        'new_count': new_count
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
