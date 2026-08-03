from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
# Секретный ключ нужен для сессий (чтобы помнил, что ты залогинен во время одной сессии)
app.secret_key = 'super_secret_key_change_me_123'

DB_NAME = 'shop.db'
ADMIN_LOGIN = 'admin'
ADMIN_PASS = '1234'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Создаём базу, если её нет
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
    # Проверяем, залогинен ли админ
    logged_in = 'admin_password' in session and session['admin_password'] == ADMIN_PASS

    # Если пришёл POST (попытка входа) и ещё не залогинен
    if request.method == 'POST' and not logged_in:
        login_attempt = request.form.get('login')
        pass_attempt = request.form.get('password')
        
        if login_attempt == ADMIN_LOGIN and pass_attempt == ADMIN_PASS:
            session['admin_password'] = ADMIN_PASS
            logged_in = True
        else:
            # Неверный логин/пароль — показываем форму входа снова
            return render_template('admin.html', logged_in=False)

    # Если всё ещё не залогинен — показываем только форму входа
    if not logged_in:
        return render_template('admin.html', logged_in=False)

    # Если залогинен — получаем все заявки из базы
    conn = get_db_connection()
    orders = conn.execute('SELECT * FROM orders ORDER BY id DESC').fetchall()
    conn.close()

    return render_template('admin.html', logged_in=True, orders=orders)

if __name__ == '__main__':
    init_db()
    # Порт берём из переменной окружения (так делает Railway), по умолчанию 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
