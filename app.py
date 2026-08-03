from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps

app = Flask(__name__)
# Секрет для работы сессий (не меняй, он нужен, чтобы сайт помнил, что ты вошёл)
app.secret_key = 'kito4kashop-super-secure-2026'

# --- НАСТРОЙКИ АДМИНОВ (МЕНЯЙ ТОЛЬКО ПАРОЛИ ЗДЕСЬ!) ---
ADMINS = {
    'banmax777': {'password': 'SUPER_SECRET_CHANGE_ME', 'role': 'main'},   # Главный
    'lox55':      {'password': 'LATER_PASSWORD_CHANGE_ME',  'role': 'helper'} # Помощник
}
# ---------------------------------------------------------

# Хранилище заявок (исчезнет при перезапуске Render — это нормально для теста)
orders = []
next_id = 1

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_role' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        user = request.form.get('user')
        password = request.form.get('password')
        
        # Проверяем, есть ли такой пользователь и совпадает ли пароль
        if user in ADMINS and ADMINS[user]['password'] == password:
            session['username'] = user
            session['user_role'] = ADMINS[user]['role']
            return redirect(url_for('admin'))
        else:
            error = 'Неверный логин или пароль!'
    
    return f'''
    <form method="POST" style="text-align:center; margin-top:50px;">
      <h2>Вход в админку kito4kashop</h2>
      <input name="user" placeholder="Логин" required style="padding:8px;"><br><br>
      <input type="password" name="password" placeholder="Пароль" required style="padding:8px;"><br><br>
      <button type="submit" style="padding:10px 20px; background:#333; color:white;">Войти</button>
      {f'<p style="color:red;">{error}</p>' if error else ''}
    </form>
    '''

@app.route('/')
def shop():
    return render_template('shop.html')

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

@app.route('/admin')
@login_required
def admin():
    username = session.get('username')
    role = session.get('user_role')
    
    # Красивая надпись в зависимости от роли
    if role == 'main':
        welcome_msg = f'🛡 Вы вошли как ГЛАВНЫЙ АДМИНИСТРАТОР ({username})'
        role_color = '#d9534f'
    else:
        welcome_msg = f'🧑‍🔧 Вы вошли как ПОМОЩНИК ({username})'
        role_color = '#5bc0de'
    
    return render_template('admin.html', orders=orders, welcome_msg=welcome_msg, role_color=role_color)

@app.route('/approve', methods=['POST'])
@login_required
def approve():
    order_id = int(request.form.get('order_id'))
    action = request.form.get('action')
    
    for order in orders:
        if order['id'] == order_id:
            order['status'] = 'approved' if action == 'approve' else 'rejected'
            break
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('shop'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
