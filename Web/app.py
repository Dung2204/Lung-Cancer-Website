import datetime
from datetime import timedelta
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify # Đã thêm jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import numpy as np
import joblib
import os
import re # Đã thêm thư viện re cho xử lý chuỗi

from .extensions import db
from .models import User, DiagnosisResult

# Khởi tạo Flask App
app = Flask(__name__)

# Cấu hình Flask App
app.secret_key = 'your_strong_secret_key_here' # Rất quan trọng: Thay đổi khóa này bằng một khóa ngẫu nhiên, mạnh mẽ
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Cấu hình Upload cho Avatar
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'avatars')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # Giới hạn 2MB cho file tải lên

# Tạo thư mục upload nếu chưa tồn tại
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Khởi tạo Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Tên hàm view cho trang đăng nhập

# Khởi tạo DB
db.init_app(app)

# Load mô hình chẩn đoán
try:
    # os.path.dirname(__file__) lấy đường dẫn thư mục hiện tại của app.py
    # 'models' là tên thư mục con chứa mô hình
    # 'lung_cancer_model.pkl' là tên file mô hình
    model_path = os.path.join(os.path.dirname(__file__), 'models', 'lung_cancer_model.pkl')
    model = joblib.load(model_path)
    print("DEBUG: Mô hình 'lung_cancer_model.pkl' đã được tải thành công.")
except Exception as e:
    print(f"Lỗi khi tải mô hình: {e}")
    model = None # Gán None nếu tải thất bại

# User loader cho Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Hàm tiện ích cho upload file ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Định nghĩa các câu trả lời cho Chatbot ---
chatbot_responses = {
    "chẩn đoán": "Để chẩn đoán nguy cơ ung thư phổi, bạn có thể vào mục 'Chẩn đoán' và điền các thông tin cần thiết. Hệ thống sẽ sử dụng mô hình AI để đưa ra kết quả.",
    "ung thư phổi": "Ung thư phổi là một loại bệnh nghiêm trọng. Ứng dụng này giúp bạn đánh giá nguy cơ dựa trên các triệu chứng. Luôn tham khảo ý kiến bác sĩ để được chẩn đoán và điều trị chính xác.",
    "triệu chứng": "Các triệu chứng phổ biến có thể bao gồm ho kéo dài, khó thở, đau ngực, sụt cân, mệt mỏi, khó nuốt. Tuy nhiên, nhiều bệnh khác cũng có các triệu chứng tương tự, vì vậy cần thăm khám bác sĩ.",
    "đăng ký": "Bạn có thể tạo tài khoản mới bằng cách nhấp vào 'Đăng ký' trên thanh điều hướng và điền thông tin theo yêu cầu.",
    "đăng nhập": "Để đăng nhập, bạn hãy nhấp vào 'Đăng nhập' trên thanh điều hướng, sau đó nhập tên tài khoản và mật khẩu của mình.",
    "lịch sử": "Bạn có thể xem lại lịch sử các lần chẩn đoán của mình trong mục 'Lịch sử chẩn đoán' sau khi đăng nhập.",
    "tài khoản": "Bạn có thể quản lý thông tin tài khoản, thay đổi email, mật khẩu, và ảnh đại diện trong trang 'Hồ sơ cá nhân'.",
    "admin": "Trang quản trị (Admin Panel) chỉ dành cho quản trị viên để quản lý người dùng và xem toàn bộ lịch sử chẩn đoán.",
    "lối sống": "Duy trì lối sống lành mạnh, không hút thuốc, hạn chế rượu, tập thể dục và chế độ ăn uống cân bằng có thể giúp giảm nguy cơ mắc bệnh.",
    "ai": "Ứng dụng này sử dụng một mô hình trí tuệ nhân tạo được huấn luyện từ dữ liệu để đánh giá nguy cơ ung thư phổi. Đây không phải là chẩn đoán y tế cuối cùng.",
    "bảo mật": "Chúng tôi cam kết bảo mật thông tin cá nhân của bạn. Dữ liệu chẩn đoán được sử dụng để cải thiện mô hình nhưng luôn được ẩn danh.",
    "liên hệ": "Nếu bạn có bất kỳ câu hỏi nào khác hoặc cần hỗ trợ, vui lòng liên hệ qua email support@lunghealthai.com hoặc số điện thoại 0123456789.",
    "cảm ơn": "Rất vui được hỗ trợ bạn! Chúc bạn luôn khỏe mạnh.",
    "tạm biệt": "Tạm biệt! Chúc bạn một ngày tốt lành và sức khỏe dồi dào.",
    "xin chào": "Xin chào! Tôi là chatbot hỗ trợ về sức khỏe phổi. Bạn có câu hỏi nào không?",
    "help": "Tôi có thể giúp bạn giải đáp các câu hỏi về ứng dụng, chẩn đoán, và thông tin chung về sức khỏe phổi.",
    "nguy cơ cao": "Nếu kết quả chẩn đoán cho thấy nguy cơ cao, điều quan trọng nhất là bạn nên đến gặp bác sĩ chuyên khoa để được thăm khám, tư vấn và làm các xét nghiệm cần thiết.",
    "mô hình": "Mô hình AI của chúng tôi được huấn luyện trên tập dữ liệu liên quan đến các yếu tố nguy cơ và triệu chứng của ung thư phổi để đưa ra dự đoán xác suất.",
}

def get_chatbot_response(user_message):
    message = user_message.lower().strip()
    
    # Ưu tiên kiểm tra các từ khóa chính xác trước
    for keyword, response in chatbot_responses.items():
        if keyword == message:
            return response
    
    # Sau đó kiểm tra các từ khóa con
    for keyword, response in chatbot_responses.items():
        if keyword in message:
            return response
            
    return "Xin lỗi, tôi không hiểu câu hỏi của bạn. Vui lòng thử hỏi lại hoặc hỏi về các chủ đề như 'chẩn đoán', 'triệu chứng', 'đăng ký', 'lịch sử', 'liên hệ'."

# --- Routes của ứng dụng (GIỮ NGUYÊN NHƯ HIỆN TẠI CỦA BẠN) ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        existing_user_email = User.query.filter_by(email=email).first()
        existing_user_username = User.query.filter_by(username=username).first()

        if existing_user_email:
            flash('Email này đã được đăng ký. Vui lòng sử dụng Email khác.', 'danger')
            return redirect(url_for('register'))
        if existing_user_username:
            flash('Tên người dùng này đã tồn tại. Vui lòng chọn tên khác.', 'danger')
            return redirect(url_for('register'))

        new_user = User(email=email, username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Đăng ký tài khoản thành công! Bây giờ bạn có thể đăng nhập.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            if user.is_banned:
                if user.ban_until is None:
                    flash('Tài khoản của bạn đã bị khóa vĩnh viễn. Vui lòng liên hệ quản trị viên.', 'danger')
                    return redirect(url_for('login'))
                elif user.ban_until > datetime.datetime.utcnow():
                    flash(f'Tài khoản của bạn đã bị khóa cho đến {user.ban_until.strftime("%H:%M %d-%m-%Y")}. Vui lòng liên hệ quản trị viên.', 'danger')
                    return redirect(url_for('login'))
            
            login_user(user, remember=True)
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Tên người dùng hoặc mật khẩu không đúng.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Bạn đã đăng xuất.', 'info')
    return redirect(url_for('index'))

@app.route('/diagnose', methods=['GET', 'POST'])
@login_required
def diagnose():
    if model is None:
        flash("Hệ thống chẩn đoán hiện không khả dụng. Vui lòng thử lại sau.", "danger")
        return redirect(url_for('index'))

    if current_user.is_banned:
        flash("Tài khoản của bạn đã bị khóa, bạn không thể thực hiện chẩn đoán.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            gender = int(request.form['gender'])
            age = int(request.form['age'])
            smoking = int(request.form['smoking'])
            yellow_fingers = int(request.form['yellow_fingers'])
            anxiety = int(request.form['anxiety'])
            peer_pressure = int(request.form['peer_pressure'])
            chronic_disease = int(request.form['chronic_disease'])
            fatigue = int(request.form['fatigue'])
            allergy = int(request.form['allergy'])
            wheezing = int(request.form['wheezing'])
            alcohol_consuming = int(request.form['alcohol_consuming'])
            coughing = int(request.form['coughing'])
            shortness_of_breath = int(request.form['shortness_of_breath'])
            swallowing_difficulty = int(request.form['swallowing_difficulty'])
            chest_pain = int(request.form['chest_pain'])

            input_data = np.array([[gender, age, smoking, yellow_fingers, anxiety,
                                    peer_pressure, chronic_disease, fatigue, allergy,
                                    wheezing, alcohol_consuming, coughing, shortness_of_breath,
                                    swallowing_difficulty, chest_pain]])
            
            prediction = model.predict(input_data)
            probability = model.predict_proba(input_data)

            prediction_result = int(prediction[0])
            probability_score = probability[0][1] * 100

            detailed_results = {
                'prediction': prediction_result,
                'probability': probability_score,
                'explanations': {
                    'overall': "Dựa trên các thông tin bạn cung cấp, đây là đánh giá nguy cơ ung thư phổi của bạn.",
                    'smoking': "Hút thuốc là một yếu tố nguy cơ lớn." if smoking == 1 else "Việc không hút thuốc giảm thiểu nguy cơ này.",
                    'age': f"Tuổi {age} cũng là một yếu tố quan trọng.",
                    'chronic_disease': "Sự hiện diện của bệnh mãn tính có thể tăng nguy cơ." if chronic_disease == 1 else "Không có bệnh mãn tính có thể giảm nguy cơ.",
                    'symptoms': "Các triệu chứng như ho, khó thở, đau ngực cần được chú ý." if any([coughing, shortness_of_breath, chest_pain]) == 1 else "Việc không có các triệu chứng rõ rệt là một dấu hiệu tốt."
                },
                'inputs': {
                    'Tuổi': age,
                    'Giới tính': 'Nam' if gender == 1 else 'Nữ',
                    'Hút thuốc': 'Có' if smoking == 1 else 'Không',
                    'Ngón tay vàng': 'Có' if yellow_fingers == 1 else 'Không',
                    'Lo âu': 'Có' if anxiety == 1 else 'Không',
                    'Áp lực bạn bè': 'Có' if peer_pressure == 1 else 'Không',
                    'Bệnh mãn tính': 'Có' if chronic_disease == 1 else 'Không',
                    'Mệt mỏi': 'Có' if fatigue == 1 else 'Không',
                    'Dị ứng': 'Có' if allergy == 1 else 'Không',
                    'Khò khè': 'Có' if wheezing == 1 else 'Không',
                    'Tiêu thụ rượu': 'Có' if alcohol_consuming == 1 else 'Không',
                    'Ho': 'Có' if coughing == 1 else 'Không',
                    'Khó thở': 'Có' if shortness_of_breath == 1 else 'Không',
                    'Khó nuốt': 'Có' if swallowing_difficulty == 1 else 'Không',
                    'Đau ngực': 'Có' if chest_pain == 1 else 'Không'
                }
            }

            new_diagnosis = DiagnosisResult(
                user_id=current_user.id,
                gender=gender,
                age=age,
                smoking=smoking,
                yellow_fingers=yellow_fingers,
                anxiety=anxiety,
                peer_pressure=peer_pressure,
                chronic_disease=chronic_disease,
                fatigue=fatigue,
                allergy=allergy,
                wheezing=wheezing,
                alcohol_consuming=alcohol_consuming,
                coughing=coughing,
                shortness_of_breath=shortness_of_breath,
                swallowing_difficulty=swallowing_difficulty,
                chest_pain=chest_pain,
                prediction=prediction_result,
                probability=probability_score
            )
            db.session.add(new_diagnosis)
            db.session.commit()

            flash('Chẩn đoán hoàn tất!', 'success')
            return render_template('result.html', detailed_results=detailed_results)

        except ValueError:
            flash("Vui lòng nhập đầy đủ và chính xác các thông tin. Các trường chỉ chấp nhận giá trị số nguyên.", "danger")
            return render_template('diagnose.html',
                gender=request.form.get('gender', ''),
                age=request.form.get('age', ''),
                smoking=request.form.get('smoking', ''),
                yellow_fingers=request.form.get('yellow_fingers', ''),
                anxiety=request.form.get('anxiety', ''),
                peer_pressure=request.form.get('peer_pressure', ''),
                chronic_disease=request.form.get('chronic_disease', ''),
                fatigue=request.form.get('fatigue', ''),
                allergy=request.form.get('allergy', ''),
                wheezing=request.form.get('wheezing', ''),
                alcohol_consuming=request.form.get('alcohol_consuming', ''),
                coughing=request.form.get('coughing', ''),
                shortness_of_breath=request.form.get('shortness_of_breath', ''),
                swallowing_difficulty=request.form.get('swallowing_difficulty', ''),
                chest_pain=request.form.get('chest_pain', '')
            )
        except KeyError as e:
            flash(f"Lỗi: Một số thông tin cần thiết bị thiếu ({e}). Vui lòng nhập đầy đủ.", "danger")
            return render_template('diagnose.html')
        except Exception as e:
            print(f"DEBUG: Đã xảy ra lỗi không xác định trong chẩn đoán: {e}")
            flash(f"Đã xảy ra lỗi trong quá trình chẩn đoán: {e}", "danger")
            return render_template('diagnose.html')
            
    return render_template('diagnose.html')


@app.route('/history')
@login_required
def history():
    user_diagnoses = DiagnosisResult.query.filter_by(user_id=current_user.id).order_by(DiagnosisResult.timestamp.desc()).all()

    formatted_diagnoses = []
    for diag in user_diagnoses:
        formatted_diagnoses.append({
            'timestamp': diag.timestamp.strftime('%H:%M %d/%m/%Y'),
            'gender': 'Nam' if diag.gender == 1 else 'Nữ',
            'age': diag.age,
            'smoking': 'Có' if diag.smoking == 1 else 'Không',
            'yellow_fingers': 'Có' if diag.yellow_fingers == 1 else 'Không',
            'anxiety': 'Có' if diag.anxiety == 1 else 'Không',
            'peer_pressure': 'Có' if diag.peer_pressure == 1 else 'Không',
            'chronic_disease': 'Có' if diag.chronic_disease == 1 else 'Không',
            'fatigue': 'Có' if diag.fatigue == 1 else 'Không',
            'allergy': 'Có' if diag.allergy == 1 else 'Không',
            'wheezing': 'Có' if diag.wheezing == 1 else 'Không',
            'alcohol_consuming': 'Có' if diag.alcohol_consuming == 1 else 'Không',
            'coughing': 'Có' if diag.coughing == 1 else 'Không',
            'shortness_of_breath': 'Có' if diag.shortness_of_breath == 1 else 'Không',
            'swallowing_difficulty': 'Có' if diag.swallowing_difficulty == 1 else 'Không',
            'chest_pain': 'Có' if diag.chest_pain == 1 else 'Không',
            'result': 'Nguy cơ cao' if diag.prediction == 1 else 'Nguy cơ thấp',
            'probability': f"{diag.probability:.2f}%"
        })
    return render_template('history.html', diagnoses=formatted_diagnoses)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', current_user=current_user)

@app.route('/change_email', methods=['POST'])
@login_required
def change_email():
    new_email = request.form['new_email']
    if not new_email:
        flash('Email mới không được để trống.', 'danger')
        return redirect(url_for('profile'))

    existing_email = User.query.filter_by(email=new_email).first()
    if existing_email and existing_email.id != current_user.id:
        flash('Email này đã được sử dụng bởi người dùng khác.', 'danger')
        return redirect(url_for('profile'))

    current_user.email = new_email
    db.session.commit()
    flash('Email của bạn đã được cập nhật thành công!', 'success')
    return redirect(url_for('profile'))

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_new_password = request.form['confirm_new_password']

    if not check_password_hash(current_user.password, current_password):
        flash('Mật khẩu hiện tại không đúng.', 'danger')
        return redirect(url_for('profile'))

    if new_password != confirm_new_password:
        flash('Mật khẩu mới và xác nhận mật khẩu không khớp.', 'danger')
        return redirect(url_for('profile'))

    if len(new_password) < 6:
        flash('Mật khẩu mới phải có ít nhất 6 ký tự.', 'danger')
        return redirect(url_for('profile'))

    current_user.password = generate_password_hash(new_password)
    db.session.commit()
    flash('Mật khẩu của bạn đã được thay đổi thành công!', 'success')
    return redirect(url_for('profile'))

@app.route('/change_avatar', methods=['POST'])
@login_required
def change_avatar():
    if 'avatar' not in request.files:
        flash('Không có file ảnh nào được chọn.', 'danger')
        return redirect(url_for('profile'))

    file = request.files['avatar']
    if file.filename == '':
        flash('Không có file ảnh nào được chọn.', 'danger')
        return redirect(url_for('profile'))

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(f"{current_user.id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            if current_user.profile_image and current_user.profile_image != 'default_avatar.png':
                old_avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_image)
                if os.path.exists(old_avatar_path):
                    os.remove(old_avatar_path)
                    print(f"DEBUG: Removed old avatar: {old_avatar_path}")

            file.save(filepath)
            current_user.profile_image = filename
            db.session.commit()
            flash('Ảnh đại diện của bạn đã được cập nhật thành công!', 'success')
        except Exception as e:
            flash(f'Lỗi khi tải lên ảnh: {e}', 'danger')
        return redirect(url_for('profile'))
    else:
        flash('Định dạng file không hợp lệ. Chỉ chấp nhận png, jpg, jpeg, gif.', 'danger')
        return redirect(url_for('profile'))


@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Bạn không có quyền truy cập trang này.', 'danger')
        return redirect(url_for('index'))
    
    users = User.query.all()

    # Xử lý tìm kiếm lịch sử chẩn đoán
    search_username = request.args.get('search_username') # Lấy tham số tìm kiếm từ URL
    
    if search_username:
        # Tìm người dùng theo tên
        user_ids_to_filter = db.session.query(User.id).filter(User.username.ilike(f'%{search_username}%')).all()
        # Chuyển đổi kết quả truy vấn thành danh sách các ID
        user_ids_to_filter = [user_id for (user_id,) in user_ids_to_filter]

        if user_ids_to_filter:
            all_diagnoses_raw = DiagnosisResult.query.filter(DiagnosisResult.user_id.in_(user_ids_to_filter)).order_by(DiagnosisResult.timestamp.desc()).all()
        else:
            all_diagnoses_raw = [] # Không tìm thấy người dùng, không có chẩn đoán
    else:
        all_diagnoses_raw = DiagnosisResult.query.order_by(DiagnosisResult.timestamp.desc()).all()

    # Định dạng lại dữ liệu cho hiển thị
    all_diagnoses_formatted = []
    for diag in all_diagnoses_raw:
        # Lấy thông tin người dùng liên quan đến chẩn đoán
        diag_user = User.query.get(diag.user_id)
        username = diag_user.username if diag_user else 'Người dùng không tồn tại'

        all_diagnoses_formatted.append({
            'username': username,
            'timestamp': diag.timestamp.strftime('%H:%M %d/%m/%Y'),
            'gender': 'Nam' if diag.gender == 1 else 'Nữ',
            'age': diag.age,
            'smoking': 'Có' if diag.smoking == 1 else 'Không',
            'yellow_fingers': 'Có' if diag.yellow_fingers == 1 else 'Không',
            'anxiety': 'Có' if diag.anxiety == 1 else 'Không',
            'peer_pressure': 'Có' if diag.peer_pressure == 1 else 'Không',
            'chronic_disease': 'Có' if diag.chronic_disease == 1 else 'Không',
            'fatigue': 'Có' if diag.fatigue == 1 else 'Không',
            'allergy': 'Có' if diag.allergy == 1 else 'Không',
            'wheezing': 'Có' if diag.wheezing == 1 else 'Không',
            'alcohol_consuming': 'Có' if diag.alcohol_consuming == 1 else 'Không',
            'coughing': 'Có' if diag.coughing == 1 else 'Không',
            'shortness_of_breath': 'Có' if diag.shortness_of_breath == 1 else 'Không',
            'swallowing_difficulty': 'Có' if diag.swallowing_difficulty == 1 else 'Không',
            'chest_pain': 'Có' if diag.chest_pain == 1 else 'Không',
            'result': 'Nguy cơ cao' if diag.prediction == 1 else 'Nguy cơ thấp',
            'probability': f"{diag.probability:.2f}%"
        })
    
    return render_template('admin.html', users=users, all_diagnoses=all_diagnoses_formatted, search_username=search_username)


@app.route('/admin/ban_user/<int:user_id>', methods=['POST'])
@login_required
def ban_user(user_id):
    if not current_user.is_admin:
        flash('Bạn không có quyền thực hiện hành động này.', 'danger')
        return redirect(url_for('index'))

    user_to_ban = User.query.get_or_404(user_id)
    if user_to_ban.is_admin:
        flash('Không thể khóa tài khoản quản trị viên.', 'danger')
        return redirect(url_for('admin_panel'))

    ban_duration = int(request.form.get('ban_duration', 0))
    if ban_duration > 0:
        user_to_ban.is_banned = True
        user_to_ban.ban_until = datetime.datetime.utcnow() + timedelta(days=ban_duration)
        flash(f'Người dùng {user_to_ban.username} đã bị khóa trong {ban_duration} ngày.', 'success')
    else:
        user_to_ban.is_banned = True
        user_to_ban.ban_until = None
        flash(f'Người dùng {user_to_ban.username} đã bị khóa vĩnh viễn.', 'success')

    db.session.commit()
    return redirect(url_for('admin_panel'))


@app.route('/admin/unban_user/<int:user_id>', methods=['POST'])
@login_required
def unban_user(user_id):
    if not current_user.is_admin:
        flash('Bạn không có quyền thực hiện hành động này.', 'danger')
        return redirect(url_for('index'))

    user_to_unban = User.query.get_or_404(user_id)
    user_to_unban.is_banned = False
    user_to_unban.ban_until = None
    db.session.commit()
    flash(f'Người dùng {user_to_unban.username} đã được mở khóa.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Bạn không có quyền thực hiện hành động này.', 'danger')
        return redirect(url_for('index'))

    user_to_delete = User.query.get_or_404(user_id)
    if user_to_delete.is_admin:
        flash('Không thể xóa tài khoản quản trị viên.', 'danger')
        return redirect(url_for('admin_panel'))

    if user_to_delete.profile_image and user_to_delete.profile_image != 'default_avatar.png':
        avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], user_to_delete.profile_image)
        if os.path.exists(avatar_path):
            os.remove(avatar_path)
            print(f"DEBUG: Removed avatar for deleted user: {avatar_path}")

    db.session.delete(user_to_delete)
    db.session.commit()
    flash(f'Người dùng {user_to_delete.username} và tất cả dữ liệu liên quan đã được xóa.', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/about')
def about():
    return render_template('about.html')

# --- Routes MỚI cho Chatbot API ---
# Route này chỉ xử lý các yêu cầu AJAX từ widget, không hiển thị trang riêng
@app.route('/chatbot_api', methods=['POST'])
def chatbot_api():
    user_message = request.json.get('message')
    if user_message:
        bot_response = get_chatbot_response(user_message)
        return jsonify({'response': bot_response})
    return jsonify({'response': 'Vui lòng gửi một tin nhắn.'}), 400


# --- Main execution block ---
if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            print(f"DEBUG: Created UPLOAD_FOLDER: {UPLOAD_FOLDER}")

        db.create_all()
        print("DEBUG: Database tables created/checked.")

        admin_username = 'admin'
        admin_password = 'adminpassword' # Đổi mật khẩu này trong môi trường sản phẩm!
        admin_email = 'admin@example.com'

        existing_admin = User.query.filter_by(username=admin_username).first()
        if not existing_admin:
            hashed_password = generate_password_hash(admin_password)
            new_admin = User(username=admin_username, email=admin_email, password=hashed_password, is_admin=True, profile_image='default_avatar.png')
            db.session.add(new_admin)
            db.session.commit()
            print(f"Người dùng admin '{admin_username}' được tạo thành công.")
        else:
            print(f"Người dùng admin '{admin_username}' đã tồn tại.")


    app.run(debug=True)





