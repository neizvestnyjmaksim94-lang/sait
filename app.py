import os
from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps

app = Flask(__name__)
# Используем переменную окружения или тестовый ключ
app.secret_key = os.environ.get('SECRET_KEY', 'kito4kashop-super-secret-2026-test')

# Логины и пароли (настраиваются в Render в Environment Variables)
ADMIN_USER_MAIN = 'banmax777'
ADMIN_PASS_MAIN = os.environ.get('ADMIN_PASS_MAIN', 'change_me_in_render')

ADMIN_USER_HELPER = 'lox55'
ADMIN_PASS_HELPER = os.environ.get('ADMIN_PASS_HELPER', 'change_me_in_render')

# Словарь для красивых названий в админке
KIT_NAMES = {
    'kit-demon-clan-1500k': 'Кит клана демона (1 500 000)',
    'kit-banmax777-130k':   'Кит banmax777 (130 000)',
    'kit-banmax777-2.0-250k':'Кит banmax777 2.0 (250 000)',
    'kit-security-70k':     'Кит сеферити (70 000)',
    'kit-demon-non-clan-120k':'Кит демона (не клан) (120 000)',
    'kit-sponsor-300k':     'Кит спонсера (300 000)',
    'kit-iqqo-300k':        'Кит iqqo (300 000)',
    'kit-bot-bot-10k':      'Кит боты бота (10 000)',
    'kit-mix-200k':         'Кит микс (200 000)',
    'kit-toxic-120k':       'Кит токсик (120 000)'
}

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

        if user == ADMIN_USER_MAIN and password == ADMIN_PASS_MAIN:
            session['username'] = user
            session['user_role'] = 'main'
            return redirect(url_for('admin'))

        if user == ADMIN_USER_HELPER and password == ADMIN_PASS_HELPER:
            session['username'] = user
            session['user_role'] = 'helper'
            return redirect(url_for('admin'))

        error = 'Неверный логин или пароль!'

    # Обратите внимание: autocomplete="off" здесь отключает всплывающее окно браузера
    return f'''
    <form method="POST" style="text-align:center; margin-top:50px;" autocomplete="off">
      <h2>Вход в админку kito4kashop</h2>
      <input name="user" placeholder="Логин" required style="padding:8px;"><br><br>
      <input type="password" name="password" placeholder="Пароль" required style="padding:8px;" autocomplete="new-password"><br><br>
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
    item_code = request.form.get('item')
    
    if nickname and item_code:
        orders.append({
            'id': next_id,
            'nickname': nickname,
            'item_code': item_code,
            'item_name': KIT_NAMES.get(item_code, item_code),
            'status': 'pending'
        })
        next_id += 1
    
    return redirect('/')

@app.route('/admin')
@login_required
def admin():
    username = session.get('username')
    role = session.get('user_role')

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
