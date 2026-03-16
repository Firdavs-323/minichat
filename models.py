from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Kontaktlar uchun yordamchi jadval (many-to-many relationship)
contacts = db.Table('contacts',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('contact_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.now)
)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    bio = db.Column(db.Text, nullable=True)
    profile_pic = db.Column(db.String(200), default='default.jpg')
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.now)
    created_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def last_seen_formatted(self):
       """Oxirgi ko'rilgan vaqtni formatlash"""
       if self.last_seen:
            return self.last_seen.strftime('%H:%M, %d.%m.%Y')
       return "Noma'lum"
    
    # Yuborilgan xabarlar
    sent_messages = db.relationship('Message', 
                                   foreign_keys='Message.sender_id',
                                   backref='sender', 
                                   lazy='dynamic')
    
    # Qabul qilingan xabarlar
    received_messages = db.relationship('Message',
                                      foreign_keys='Message.receiver_id',
                                      backref='receiver',
                                      lazy='dynamic')
    
    # Kontaktlar (user.contacts orqali olinadi)
    contact_list = db.relationship('User', 
                                 secondary=contacts,
                                 primaryjoin=(contacts.c.user_id == id),
                                 secondaryjoin=(contacts.c.contact_id == id),
                                 backref=db.backref('added_by', lazy='dynamic'),
                                 lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def add_contact(self, user):
        if not self.is_contact(user):
            self.contact_list.append(user)
            return True
        return False
    
    def remove_contact(self, user):
        if self.is_contact(user):
            self.contact_list.remove(user)
            return True
        return False
    
    def is_contact(self, user):
        return self.contact_list.filter(contacts.c.contact_id == user.id).count() > 0
    
    def get_contacts(self):
        return self.contact_list.all()
    
    def get_unread_messages_count(self):
        return Message.query.filter_by(receiver_id=self.id, is_read=False).count()
    
    def __repr__(self):
        return f'<User {self.username}>'

class Message(db.Model):
    __tablename__ = 'message'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    is_read = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Message {self.id}: {self.sender_id} -> {self.receiver_id}>'

class Notification(db.Model):
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50))  # 'contact_request', 'message', 'system'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    link = db.Column(db.String(200))
    
    user = db.relationship('User', backref='notifications')