from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('orders.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Создаёт таблицу, если её нет"""
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

# Инициализируем БД при старте
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
    order_id = request.args.get('order_id')
    if not order_id:
        return "Нет ID заказа", 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
    order = cur.fetchone()
    conn.close()

    if not order:
        return "Заказ не найден", 404

    return render_template(
        'thanks.html',
        order_id=order.id,
        nickname=order.nickname,
        item=order.item,
        status=order.status,
        admin_comment=order.admin_comment or ''
    )

@app.route('/admin')
def admin():
    # Защита теперь на стороне Render, тут просто отдаём страницу
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM orders ORDER BY id DESC')
    orders = cur.fetchall()
    conn.close()
    return render_template('admin.html', orders=orders)

@app.route('/admin/accept/<int:order_id>', methods=['POST'])
def accept_order(order_id):
    print(f"[DEBUG] Принят заказ #{order_id}")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE orders SET status = ? WHERE id = ?', ('accepted', order_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/reject/<int:order_id>', methods=['POST'])
def reject_order(order_id):
    comment = request.form.get('comment', '')
    print(f"[DEBUG] Отклонён заказ #{order_id}, комментарий: {comment}")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE orders SET status = ?, admin_comment = ? WHERE id = ?',
                ('rejected', comment, order_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
