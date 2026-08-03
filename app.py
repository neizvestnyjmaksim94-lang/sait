from flask import Flask, render_template, request, session
import sqlite3
import os

app = Flask(__name__)

# Секрет для сессий: из Render или запасной
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_change_me_123')

DB_NAME = 'shop.db'

# Пароли берём из настроек Render. Если нет — ставим по умолчанию
PASS_LOX55 = os.environ.get('ADMIN_PASS_LOX55', 'lox55pass')
PASS_BANMAX = os.environ.get('ADMIN_PASS_BANMAX', 'banmaxpass')

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT NOT NULL,
            item TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def shop():
    return render_template('shop.html')

@app.route('/buy', methods=['POST'])
def buy():
    nickname = request.form.get('nickname')
    item = request.form.get('item')
    
    if not nickname or not item:
        return "Ошибка: заполни все поля!", 400

    conn = get_db_connection()
    conn.execute('INSERT INTO orders (nickname, item, status) VALUES (?, ?, ?)',
                 (nickname, item, 'pending'))
    conn.commit()
    conn.close()
    
    return "Заявка отправлена! Менеджер свяжется с тобой."

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # Сессия хранит тип аккаунта: 'helper' или 'main'
    account_type = session.get('account_type')

    if request.method == 'POST':
        login_attempt = request.form.get('login')
        pass_attempt = request.form.get('password')

        # Проверка для lox55 (помощник)
        if login_attempt == 'lox55' and pass_attempt == PASS_LOX55:
            session['account_type'] = 'helper'
            return render_template('admin.html', logged_in=True, account_type='helper')

        # Проверка для banmax777 (главный)
        if login_attempt == 'banmax777' and pass_attempt == PASS_BANMAX:
            session['account_type'] = 'main'
            return render_template('admin.html', logged_in=True, account_type='main')

        # Если логин/пароль не подошли — показываем форму входа
        return render_template('admin.html', logged_in=False, account_type=None)

    # Если не POST, а просто GET — показываем то, что уже в сессии
    if account_type:
        conn = get_db_connection()
        orders = conn.execute('SELECT * FROM orders ORDER BY id DESC').fetchall()
        conn.close()
        return render_template('admin.html', logged_in=True, account_type=account_type, orders=orders)

    # Если сессии нет — форма входа
    return render_template('admin.html', logged_in=False, account_type=None)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
