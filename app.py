from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import boto3

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@mysql_host/database_name'
app.config['SECRET_KEY'] = ''
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
# Amazon Web Services credentials
AWS_ACCESS_KEY_ID = 'your access key id'
AWS_SECRET_ACCESS_KEY = 'your secret access key'

# Amazon Simple Email Service
SES_REGION_NAME = 'us-west-2'  # change to match your region
SES_EMAIL_SOURCE = 'example.email@example.com'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Integer)
    count_producct_search = db.Column(db.Integer, default=0)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    brand = db.Column(db.String(50), nullable=False)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user = User.query.filter_by(email=email, password=password).first()
    if user:
        login_user(user)
        return jsonify(message='Login successful')
    return jsonify(message='Invalid credentials'), 401


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify(message='Logout successful')


@app.route('/products/<int:user_id>', methods=['GET', 'POST'])
@login_required
def products(user_id):
    # role 1: admin, role 2: anonymus
    user = Product.query.get(user_id)
    if request.method == 'GET':
        products = Product.query.all()
        if user.role == 2:
            user.count_producct_search += 1
        return jsonify(products=[product.serialize() for product in products])
    elif request.method == 'POST':
        if user.role == 1:
            data = request.get_json()
            sku = data.get('sku')
            name = data.get('name')
            price = data.get('price')
            brand = data.get('brand')
            product = Product(sku=sku, name=name, price=price, brand=brand)
            db.session.add(product)
            db.session.commit()
            notify_admins(f'New product added: {sku}')
            return jsonify(message='Product added successfully')
        elif user.role == 2:
            return jsonify(message='You cant add new product')


@app.route('/products/<int:user_id>', methods=['PUT', 'DELETE'])
@login_required
def product(user_id):
    user = User.query.get(user_id)
    emails_admins = user.email

    if not product:
        return jsonify(message='Product not found'), 404
    if request.method == 'GET':
        
        db.session.commit()
        return jsonify(product.serialize())
    elif request.method == 'PUT':
        if user.role == 1:
            data = request.get_json()
            product.sku = data.get('sku', product.sku)
            product.name = data.get('name', product.name)
            product.price = data.get('price', product.price)
            product.brand = data.get('brand', product.brand)
            db.session.commit()
            notify_admins('', emails_admins, 'update product', 'update product', '')
            return jsonify(message='Product updated successfully')
        elif user.role == 2:
            return jsonify(message='You cant update a product')
    elif request.method == 'DELETE':
        if user.role == 1:
            db.session.delete(product)
            db.session.commit()
            notify_admins(f'Product deleted: {product.sku}')
            return jsonify(message='Product deleted successfully')
        elif user.role == 2:
            return jsonify(message='You cant delete a product')


def notify_admins(app, recipients, sender=None, subject='', text='', html=''):
    ses = boto3.client(
        'ses',
        region_name=SES_REGION_NAME,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    if not sender:
        sender =SES_EMAIL_SOURCE

    ses.send_email(
        Source=sender,
        Destination={'ToAddresses': recipients},
        Message={
            'Subject': {'Data': subject},
            'Body': {
                'Text': {'Data': text},
                'Html': {'Data': html}
            }
        }
    )

if __name__ == '__main__':
    app.run(debug=True)
