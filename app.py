import os
from flask import Flask, render_template, request, redirect, url_for, session
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

app = Flask(__name__)

# SECRET_KEY: обязательно поставь в Render!
secret_key_env = os.environ.get('SECRET_KEY')
if not secret_key_env:
    app.secret_key = 'dev-only-key-change-on-render'
else:
    app.secret_key = secret_key_env

# DATABASE_URL: берём из Render
db_url = os.getenv('DATABASE_URL')
if db_url and db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

if not db_url:
    raise ValueError("Ошибка: не найдена переменная DATABASE_URL в настройках Render!")

engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nickname = Column(String)
    item = Column(String)
    status = Column(String, default='pending')
    admin_comment = Column(String, nullable=True)  # <-- комментарий админа при отказе

with app.app_context():
    Base.metadata.create_all(engine)

# Пароли берём из переменных окружения (Render)
PASS_LOX55 = os.environ.get('ADMIN_PASS_LOX55')
PASS_BANMAX = os.environ.get('ADMIN_PASS_BANMAX')

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

    return redirect(url_for('order_status', order_id=order_id))

@app.route('/order-status/<int:order_id>')
def order_status(order_id):
    db = SessionLocal()
    try:
        order = db.query(Order).filter_by(id=order_id).first()
    finally:
        db.close()

    if not order:
        return "Заказ не найден", 404

    return render_template(
        'thanks.html',
        nickname=order.nickname,
        item=order.item,
        status=order.status,
        admin_comment=order.admin_comment,  # <-- передаём комментарий
        order_id=order.id
    )

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    account_type = session.get('account_type')

    # Если пришли с POST — попытка входа
    if request.method == 'POST':
        login_attempt = request.form.get('login')
        pass_attempt = request.form.get('password')

        if login_attempt == 'lox55' and pass_attempt == PASS_LOX55:
            session['account_type'] = 'helper'
            return redirect(url_for('admin'))

        if login_attempt == 'banmax777' and pass_attempt == PASS_BANMAX:
            session['account_type'] = 'main'
            return redirect(url_for('admin'))

        return render_template('admin.html', logged_in=False, account_type=None, error="Неверный логин или пароль")

    # Если уже залогинен — показываем админку
    if account_type:
        db = SessionLocal()
        try:
            orders = db.query(Order).filter_by(status='pending').order_by(Order.id.desc()).all()
        finally:
            db.close()
        return render_template('admin.html', logged_in=True, account_type=account_type, orders=orders)

    # Не залогинен и не POST — показываем форму входа
    return render_template('admin.html', logged_in=False, account_type=None, error=None)

@app.route('/admin/update_status', methods=['POST'])
def update_status():
    if not session.get('account_type'):
        return redirect(url_for('admin'))

    order_id = request.form.get('order_id')
    new_status = request.form.get('new_status')
    comment = request.form.get('admin_comment')  # <-- читаем комментарий

    if not order_id or new_status not in ('accepted', 'rejected'):
        return "Неверные данные", 400

    db = SessionLocal()
    try:
        order = db.query(Order).filter_by(id=order_id).first()
        if not order:
            return "Заказ не найден", 404

        order.status = new_status
        if comment:
            order.admin_comment = comment
        db.commit()
    except Exception as e:
        db.rollback()
        return f"Ошибка: {e}", 500
    finally:
        db.close()

    return redirect(url_for('admin'))

@app.route('/admin/logout')
def logout():
    session.clear()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
