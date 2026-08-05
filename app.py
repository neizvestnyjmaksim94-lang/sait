import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, abort
import sqlite3

app = Flask(__name__)
# Обязательно поставь случайную строку в Render как переменную SECRET_KEY
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-render')

def get_db_connection():
    conn = sqlite3.connect('orders.db', timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT NOT NULL,
            item TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            admin_comment TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def shop():
    return render_template('shop.html')

@app.route('/buy', methods=['POST'])
def buy():
    nickname = request.form.get('nickname', '').strip()
    item = request.form.get('item', '').strip()
    if not nickname or not item:
        return redirect(url_for('shop'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO orders (nickname, item, status) VALUES (?, ?, ?)',
                (nickname, item, 'pending'))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return redirect(url_for('thanks', order_id=new_id))

@app.route('/thanks')
def thanks():
    order_id_param = request.args.get('order_id')
    if not order_id_param:
        return "Нет ID заказа", 400
    try:
        order_id = int(order_id_param)
    except ValueError:
        return "Неверный ID заказа", 400
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
    order = cur.fetchone()
    conn.close()
    if not order:
        return "Заказ не найден", 404
    return render_template(
        'thanks.html',
        order_id=order['id'],
        nickname=order['nickname'],
        item=order['item'],
        status=order['status'],
        admin_comment=order['admin_comment'] or ''
    )

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error = None
    orders = []
    
    # Если это POST (попытка входа)
    if request.method == 'POST':
        login = request.form.get('login', '').strip()
        password = request.form.get('password', '').strip()

        pass_banmax = os.environ.get('ADMIN_PASS_BANMAX', '')
        pass_lox55 = os.environ.get('ADMIN_PASS_LOX55', '')

        if (login == 'banmax' and password == pass_banmax) or \
           (login == 'lox55' and password == pass_lox55):
            session['admin_logged_in'] = True
            session['admin_user'] = login
            # Если вход успешен, сразу грузим заказы
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT * FROM orders ORDER BY id DESC')
            orders = cur.fetchall()
            conn.close()
        else:
            error = "Неверный логин или пароль"

    # Если это GET и пользователь уже залогинен — сразу грузим заказы
    if request.method == 'GET' and session.get('admin_logged_in'):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM orders ORDER BY id DESC')
        orders = cur.fetchall()
        conn.close()

    # Если есть заказы (успешный вход или уже залогинен) — показываем админку
    if orders:
        return render_template('admin.html', orders=orders)
    
    # Если заказов нет — показываем форму входа
    return render_template('admin.html', error=error)

@app.route('/admin/accept/<int:order_id>', methods=['POST'])
def accept_order(order_id):
    if not session.get('admin_logged_in'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE orders SET status = ? WHERE id = ?', ('accepted', order_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'order_id': order_id, 'new_status': 'accepted'})

@app.route('/admin/reject/<int:order_id>', methods=['POST'])
def reject_order(order_id):
    if not session.get('admin_logged_in'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    comment = request.form.get('comment', '')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE orders SET status = ?, admin_comment = ? WHERE id = ?',
                ('rejected', comment, order_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'order_id': order_id, 'new_status': 'rejected'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
