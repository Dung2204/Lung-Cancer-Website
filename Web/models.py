from datetime import datetime
from flask_login import UserMixin
from extensions import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    profile_image = db.Column(db.String(255), default='default_avatar.png')
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    ban_until = db.Column(db.DateTime, nullable=True)

    diagnosis_results = db.relationship('DiagnosisResult', backref='user', lazy=True, cascade="all, delete-orphan")

class DiagnosisResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Các trường dữ liệu đầu vào chẩn đoán
    gender = db.Column(db.Integer, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    smoking = db.Column(db.Integer, nullable=False)
    yellow_fingers = db.Column(db.Integer, nullable=False)
    anxiety = db.Column(db.Integer, nullable=False)
    peer_pressure = db.Column(db.Integer, nullable=False)
    chronic_disease = db.Column(db.Integer, nullable=False)
    fatigue = db.Column(db.Integer, nullable=False)
    allergy = db.Column(db.Integer, nullable=False)
    wheezing = db.Column(db.Integer, nullable=False)
    alcohol_consuming = db.Column(db.Integer, nullable=False)
    coughing = db.Column(db.Integer, nullable=False)
    shortness_of_breath = db.Column(db.Integer, nullable=False)
    swallowing_difficulty = db.Column(db.Integer, nullable=False)
    chest_pain = db.Column(db.Integer, nullable=False)
    # Kết quả chẩn đoán
    prediction = db.Column(db.Integer, nullable=False) # 0 hoặc 1
    probability = db.Column(db.Float, nullable=False) # <-- THÊM DÒNG NÀY
    # Các trường khác có thể bạn muốn lưu
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<DiagnosisResult {self.id} for User {self.user_id} - Pred: {self.prediction}>'