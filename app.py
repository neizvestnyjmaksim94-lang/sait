import os
from flask import Flask, render_template, request, session
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_change_me_123')

# Получаем URL из переменной окружения (Render подставит её автоматически)
db_url = os.getenv('DATABASE_URL')

# Исправляем префикс, если нужно: postgres:// -> postgresql://
if db_url and db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

# Настраиваем SQLAlchemy
engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Модель таблицы orders
class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nickname = Column(String)
    item = Column(String)
    status = Column(String, default='pending')

# Создаём таблицы при старте (если их ещё нет)
with app.app_context():
    Base.metadata.create_all(engine)

# Пароли из переменных окружения (или дефолтные для тестов)
PASS_LOX55 = os.environ.get('ADMIN_PASS_LOX55', 'loxlox123')
PASS_BANMAX = os.environ.get('ADMIN_PASS_BANMAX', 'banban123')

@app.route('/')
def shop():
    return render_template('shop.html')

@app.route('/buy', methods=['POST'])
def buy():
    nickname = request.form.get('nickname')
    item = request.form.get('item')
    
    if not nickname or not item:
        return "Ошибка: заполни все поля!", 400

    db = SessionLocal()
    try:
        new_order = Order(nickname=nickname, item=item, status='pending')
        db.add(new_order)
        db.commit()
        order_id = new_order.id
    except Exception as e:
        db.rollback()
        return f"Ошибка при сохранении заказа: {e}", 500
    finally:
        db.close()

    return render_template('thanks.html', nickname=nickname, item=item, status='Ожидает обработки', order_id=order_id)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    account_type = session.get('account_type')

    if request.method == 'POST':
        login_attempt = request.form.get('login')
        pass_attempt = request.form.get('password')

        if login_attempt == 'lox55' and pass_attempt == PASS_LOX55:
            session['account_type'] = 'helper'
            return render_template('admin.html', logged_in=True, account_type='helper')

        if login_attempt == 'banmax777' and pass_attempt == PASS_BANMAX:
            session['account_type'] = 'main'
            return render_template('admin.html', logged_in=True, account_type='main')

        return render_template('admin.html', logged_in=False, account_type=None)

    if account_type:
        db = SessionLocal()
        try:
            orders = db.query(Order).order_by(Order.id.desc()).all()
        finally:
            db.close()
        return render_template('admin.html', logged_in=True, account_type=account_type, orders=orders)

    return render_template('admin.html', logged_in=False, account_type=None)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
