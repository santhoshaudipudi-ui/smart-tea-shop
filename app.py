from flask import Flask, render_template, request, jsonify, redirect, session, url_for
import os
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)

# SECRET KEY
app.secret_key = "ganesh_secret_tea_shop"

# SESSION CONFIG
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'ganesh_tea.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# DATABASE
db = SQLAlchemy(app)


# DATABASE MODEL
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))
    tea_name = db.Column(db.String(500))
    price = db.Column(db.Integer)
    status = db.Column(db.String(50), default='Preparing...')
    rating = db.Column(db.Integer, default=0)
    order_date = db.Column(db.Date, default=date.today)
    timestamp = db.Column(db.DateTime, default=datetime.now)


with app.app_context():
    db.create_all()


# LOGIN REQUIRED DECORATOR

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('owner_logged_in'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


# CUSTOMER PAGE
@app.route('/')
def index():
    return render_template('customer.html')


# PLACE ORDER
@app.route('/place_order', methods=['POST'])
def place_order():
    data = request.json

    new_o = Order(
        customer_name=data['name'],
        tea_name=data['tea'],
        price=data['total']
    )

    db.session.add(new_o)
    db.session.commit()

    return jsonify({"id": new_o.id})


# FEEDBACK
@app.route('/submit_feedback', methods=['POST'])
def feedback():
    data = request.json

    o = Order.query.get(data['id'])

    if o:
        o.rating = data['rating']
        db.session.commit()

    return jsonify({"status": "ok"})


# LOGIN PAGE
@app.route('/login', methods=['GET', 'POST'])
def login():

    error = ""

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        # CHANGE THESE VALUES
        if username == 'ganesh' and password == 'tea123':
            session['owner_logged_in'] = True
            return redirect('/owner')
        else:
            error = 'Invalid Username or Password'

    return render_template('login.html', error=error)


# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# OWNER DASHBOARD
@app.route('/owner')
@login_required
def owner():
    return render_template('owner.html')


# ADMIN DATA
@app.route('/admin/data')
@login_required
def admin_data():

    orders = Order.query.order_by(Order.timestamp.desc()).all()

    today = date.today()

    daily = sum(o.price for o in orders if o.order_date == today)

    monthly = sum(o.price for o in orders if o.order_date.month == today.month)

    history = [
        {
            'id': o.id,
            'name': o.customer_name,
            'tea': o.tea_name,
            'price': o.price,
            'status': o.status,
            'rating': o.rating
        }
        for o in orders
    ]

    return jsonify({
        'history': history,
        'daily': daily,
        'monthly': monthly
    })


# UPDATE STATUS
@app.route('/update_status/<int:id>/<string:mode>', methods=['POST'])
@login_required
def update_status(id, mode):

    o = Order.query.get(id)

    if o:
        if mode == 'ready':
            o.status = 'READY ✅'
        elif mode == 'delay':
            o.status = '5 Min Delay ⏳'
        elif mode == 'completed':
            o.status = 'COMPLETED ✔'

    db.session.commit()

    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)