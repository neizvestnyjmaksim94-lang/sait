from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps

app = Flask(__name__)
app.secret_key = 'kito4kashop-secret-key-change-later'  # нужен для работы сессий

# Простая база заявок (в памяти, исчезнет после перезапуска, но для теста идеально)
orders = []
next_id = 1

# --- Защита админки (Basic Auth) ---
ADMIN_USER = 'admin'
ADMIN_PASS = '12345'  # ⚠️ Поставь свой пароль!

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        user = request.form.get('user')
        password = request.form.get('password')
        if user == ADMIN_USER and password == ADMIN_PASS:
            session['is_admin'] = True
            return redirect(url_for('admin'))
    return '''
    <form method="POST">
      <h2>Вход в админку kito4kashop</h2>
      <input name="user" placeholder="Логин" required><br><br>
      <input type="password" name="password" placeholder="Пароль" required><br><br>
      <button type="submit">Войти</button>
    </form>
    '''

@app.route('/')
def shop():
    return render_template('shop.html')

# Обработка заявки на покупку
@app.route('/buy', methods=['POST'])
def buy():
    global next_id
    nickname = request.form.get('nickname')
    item = request.form.get('item')
    if nickname and item:
        orders.append({
            'id': next_id,
            'nickname': nickname,
            'item': item,
            'status': 'pending'
        })
        next_id += 1
    return redirect('/')

# Страница админки
@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html', orders=orders)

# Одобрить или отклонить заявку
@app.route('/approve', methods=['POST'])
@login_required
def approve():
    order_id = int(request.form.get('order_id'))
    action = request.form.get('action')  # 'approve' или 'reject'
    
    for order in orders:
        if order['id'] == order_id:
            order['status'] = 'approved' if action == 'approve' else 'rejected'
            break
    return redirect(url_for('admin'))

# Выход из админки
@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('shop'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
