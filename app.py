import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy

# Создаём приложение один раз
app = Flask(__name__)

# Получаем абсолютный путь к директории, где находится этот скрипт
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Папки data и logs на Render не нужны: там файловая система временная,
# а логи лучше писать в stdout (в консоль Render), а не в файл.
# Поэтому эти строки можно убрать:
# os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)
# os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# База данных: на бесплатном Render SQLite не годится для сохранения данных,
# потому что файлы стираются при перезапуске. Для теста можно оставить,
# но помни, что данные пропадут.
db_path = os.path.join(BASE_DIR, 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

# SECRET_KEY берём из переменной окружения, если её нет — ставим заглушку
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

db = SQLAlchemy(app)

# Настройка логирования: пишем в консоль (так Render покажет логи), не в файл
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Модель заявки
class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), default='pending')
    amount = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'status': self.status,
            'amount': self.amount,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

# Создание таблиц: делаем это не при импорте, а при первом запросе или отдельно.
# На бесплатном Render с SQLite это всё равно не даст постоянного хранения,
# но для теста можно оставить так:
with app.app_context():
    db.create_all()
    logging.info("Таблицы базы данных созданы (или проверены)")

# Пароль админа: берём из переменной окружения
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'пук в баночке')  # пока можно так, но лучше сменить на случайную строку

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/waiting')
def waiting():
    username = request.args.get('username')
    if not username:
        return "Ошибка: имя пользователя не указано", 400
    return render_template('waiting.html', username=username)

@app.route('/api/submit', methods=['POST'])
def submit_request():
    data = request.get_json()
    username = data.get('username')

    if not username:
        return jsonify({'message': 'Имя обязательно'}), 400

    existing = Request.query.filter_by(username=username, status='pending').first()
    if existing:
        logging.warning(f'Дублирующая заявка от {username}')
        return jsonify({'message': 'Заявка уже в ожидании'}), 400

    new_request = Request(username=username)
    db.session.add(new_request)
    try:
        db.session.commit()
        logging.info(f'Заявка от {username} создана')
        return jsonify({
            'message': 'Заявка отправлена, ожидайте',
            'redirect': f'/waiting?username={username}'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f'Ошибка сохранения заявки от {username}: {e}')
        return jsonify({'message': 'Ошибка сохранения заявки'}), 500

@app.route('/api/status')
def check_status():
    username = request.args.get('username')
    request_obj = Request.query.filter_by(username=username).order_by(Request.id.desc()).first()

    if request_obj:
        return jsonify({
            'status': request_obj.status,
            'amount': request_obj.amount
        })
    else:
        return jsonify({'status': 'not_found'})

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    password = data.get('password')

    if password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        logging.info('Админ вошёл в систему')
        return jsonify({'success': True})
    else:
        logging.warning('Неудачная попытка входа админа')
        return jsonify({'success': False}), 401

@app.route('/api/admin/requests')
def get_requests():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Не авторизован'}), 403

    pending_requests = Request.query.filter_by(status='pending').all()
    return jsonify([req.to_dict() for req in pending_requests])

@app.route('/api/admin/approve/<int:request_id>', methods=['POST'])
def approve_request(request_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Не авторизован'}), 403

    data = request.get_json()
    amount = int(data.get('amount', 0))
    rounded_amount = round(amount)

    request_obj = Request.query.get(request_id)
    if request_obj:
        request_obj.status = 'approved'
        request_obj.amount = rounded_amount
        try:
            db.session.commit()
            logging.info(f'Заявка {request_id} одобрена на сумму {rounded_amount} руб.')
            return jsonify({'success': True, 'message': f'Заявка одобрена на {rounded_amount} руб.'})
        except Exception as e:
            db.session.rollback()
            logging.error(f'Ошибка сохранения одобрения заявки {request_id}: {e}')
            return jsonify({'error': 'Ошибка сохранения в базе данных'}), 500
    else:
        logging.error(f'Попытка одобрения несуществующей заявки {request_id}')
        return jsonify({'error': 'Заявка не найдена'}), 404

@app.route('/api/admin/reject/<int:request_id>', methods=['POST'])
def reject_request(request_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Не авторизован'}), 403

    request_obj = Request.query.get(request_id)
    if request_obj:
        try:
            db.session.delete(request_obj)
            db.session.commit()
            logging.info(f'Заявка {request_id} отклонена и удалена')
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            logging.error(f'Ошибка удаления заявки {request_id}: {e}')
            return jsonify({'error': 'Ошибка удаления заявки'}), 500
    else:
        logging.error(f'Попытка отклонения несуществующей заявки {request_id}')
        return jsonify({'error': 'Заявка не найдена'}), 404

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin_logged_in', None)
    logging.info('Админ вышел из системы')
    return jsonify({'success': True})

# Строку if __name__ == '__main__': и app.run НЕ добавляем.
# Render запустит приложение через Gunicorn.
