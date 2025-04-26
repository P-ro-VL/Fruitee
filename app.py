from flask import Flask, jsonify, render_template, request, session, redirect

import os
import sqlite3

app = Flask(__name__)
app.template_folder = 'templates'
app.static_folder = os.path.abspath('static')
app.secret_key = 'fruitee'

SHIPPING_FEE = 0

@app.route('/')
def index():
    return render_template('index.html', user=session['user']['name'] if 'user' in session else None)

@app.route('/shop')
def shop():
    query = request.args.get('query')
    if query:
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()

        cursor.execute('SELECT * FROM fruits WHERE name LIKE ?', ('%' + query + '%',))
        products = cursor.fetchall()
        connection.close()

        return render_template('shop.html', products=products)

    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM fruits')
    products = cursor.fetchall()
    connection.close()

    return render_template('shop.html', products=products, user=session['user']['name'] if 'user' in session else None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()

        cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        user = cursor.fetchone()
        connection.close()

        if user:
            session['user'] = {
                'id': user[0],
                'name': user[1],
                'username': user[2],
            }
            return render_template('index.html', user=user[1])
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html', user=session['user']['name'] if 'user' in session else None)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/', code=200)

@app.route('/add/<fruit_id>', methods=['POST'])
def add_to_cart(fruit_id):
    if 'user' not in session:
        return redirect('/login', code=302)

    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM fruits WHERE id=?', (fruit_id,))
    fruit = cursor.fetchone()
    connection.close()

    if fruit:
        cart = session.get('cart', [])
        for item in cart:
            if item['id'] == fruit[0]:
                item['quantity'] += 1
                item['total_price'] += fruit[2]
                break
        else:
            cart.append({
                'id': fruit[0],
                'name': fruit[1],
                'price': fruit[2],
                'quantity': 1,
                'total_price': fruit[2],
            })
        session['cart'] = cart
        return redirect('/shop', code=302)
    else:
        return redirect('/shop', code=404)
    
@app.route('/cart/<fruit_id>', methods=['POST'])
def remove_from_cart(fruit_id):
    if 'user' not in session:
        return redirect('/login', code=302)

    cart = session.get('cart', [])
    for item in cart:
        if item['id'] == int(fruit_id):
            cart.remove(item)
            break
    session['cart'] = cart
    return redirect('/shop', code=302)

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if 'user' not in session:
        return redirect('/login', code=302)
    
    discount = 0
    couponName = None

    if request.method == 'POST':
        action = request.args.get('action')
        fruit_id = request.args.get('product_id')

        cart = session.get('cart', [])

        if action == 'remove':
            for item in cart:
                if item['id'] == fruit_id:
                    item['quantity'] -= 1
                    item['total_price'] -= item['price']
                    if item['quantity'] <= 0:
                        cart.remove(item)
        else:
            for item in cart:
                if item['id'] == fruit_id:
                    item['quantity'] += 1
                    item['total_price'] += item['price']

        session['cart'] = cart
        print(cart)
    else:
        coupon_code = request.args.get('coupon_code')

        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()

        cursor.execute('SELECT * FROM coupons')
        coupons = cursor.fetchall()
        connection.close()

        for coupon in coupons:
            if coupon[1] == coupon_code:
                discount = coupon[2]
                couponName = coupon[1]
                break

    cart = session.get('cart', [])
    total_price = sum(item['total_price'] for item in cart)
    total_cart = total_price

    discount = (discount / 100) * total_price
    total_price -= discount
    total_price += SHIPPING_FEE

    return render_template('cart.html', cart=cart, coupon_name=couponName, total_cart=total_cart, discount=discount, shipping_fee=SHIPPING_FEE, total_price=total_price, user=session['user']['name'] if 'user' in session else None)

@app.route('/payment', methods=['POST', 'GET'])
def payment():
    if 'user' not in session:
        return redirect('/login', code=302)
    
    if request.method == 'POST':
        total_price = request.json['total_price']
        session['payment'] = total_price
    
    print(session['payment'])

    return render_template('payment.html', total_price=session['payment'], user=session['user']['name'] if 'user' in session else None)

if __name__ == '__main__':
    print(app.static_folder)
    app.run(debug=True)