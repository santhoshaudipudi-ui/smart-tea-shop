from flask import Flask, render_template, request, jsonify
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'ganesh_tea.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))
    tea_name = db.Column(db.String(500))
    price = db.Column(db.Integer)
    status = db.Column(db.String(50), default='Preparing...')
    rating = db.Column(db.Integer, default=0) # Feedback column
    order_date = db.Column(db.Date, default=date.today)
    timestamp = db.Column(db.DateTime, default=datetime.now)

with app.app_context():
    db.create_all()

@app.route('/')
def index(): return render_template('customer.html')

@app.route('/place_order', methods=['POST'])
def place_order():
    data = request.json
    new_o = Order(customer_name=data['name'], tea_name=data['tea'], price=data['total'])
    db.session.add(new_o)
    db.session.commit()
    return jsonify({"id": new_o.id})

# NEW FEEDBACK ROUTE
@app.route('/submit_feedback', methods=['POST'])
def feedback():
    data = request.json
    o = Order.query.get(data['id'])
    if o:
        o.rating = data['rating']
        db.session.commit()
    return jsonify({"status": "ok"})

@app.route('/owner')
def owner(): return render_template('owner.html')

@app.route('/admin/data')
def admin_data():
    orders = Order.query.order_by(Order.timestamp.desc()).all()
    today = date.today()
    daily = sum(o.price for o in orders if o.order_date == today)
    monthly = sum(o.price for o in orders if o.order_date.month == today.month)
    history = [{'id':o.id, 'name':o.customer_name, 'tea':o.tea_name, 'price':o.price, 'status':o.status, 'rating':o.rating} for o in orders]
    return jsonify({'history': history, 'daily': daily, 'monthly': monthly})

@app.route('/update_status/<int:id>/<string:mode>', methods=['POST'])
def update_status(id, mode):
    o = Order.query.get(id)
    if o:
        if mode == 'ready': o.status = 'READY ✅'
        elif mode == 'delay': o.status = '5 Min Delay ⏳'
    db.session.commit()
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)