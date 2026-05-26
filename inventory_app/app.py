import os
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt,
)
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash

# -----------------------------
# Inventory Management System
# Lightweight Flask backend + SQLite for mobile-friendly inventory app.
# Architecture:
# - Single Flask app (fast to deploy, easy to open in Visual Studio / NetBeans)
# - SQLite database via SQLAlchemy (file-based, low-cost, portable)
# - JWT-based auth with roles: cashier, supervisor, manager, admin
# - Models: User, Branch, Product, ProductStock, Sale, SaleItem
# - API endpoints below (see each route's docstring for details)
# -----------------------------

app = Flask(__name__)
instance_dir = os.path.join(app.root_path, 'instance')
os.makedirs(instance_dir, exist_ok=True)
db_path = os.path.join(instance_dir, 'inventory.db')
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.abspath(db_path).replace('\\', '/')}" )
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-me")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=int(os.environ.get("JWT_ACCESS_TOKEN_HOURS", "1")))
app.config["ENABLE_DB_INIT"] = os.environ.get("ENABLE_DB_INIT", "false").lower() == "true"
app.config["DB_INIT_SECRET"] = os.environ.get("DB_INIT_SECRET", "")
app.config["FLASK_DEBUG"] = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
app.config["JWT_COOKIE_SECURE"] = os.environ.get("FLASK_ENV", "development").lower() == "production"
app.config["MAX_FAILED_LOGIN_ATTEMPTS"] = int(os.environ.get("MAX_FAILED_LOGIN_ATTEMPTS", "5"))

db = SQLAlchemy(app)
jwt = JWTManager(app)


# -----------------------------
# Database models (schema)
# - User: app users with role and optional branch association
# - Branch: stores for multi-branch support
# - Product: master product catalog
# - ProductStock: per-branch stock levels + reorder threshold
# - Sale: sales transactions (header)
# - SaleItem: items belonging to a sale
# -----------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(32), nullable=False)  # cashier/supervisor/manager/admin
    full_name = db.Column(db.String(120), nullable=True)
    sex = db.Column(db.String(16), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True)
    locked = db.Column(db.Boolean, nullable=False, default=False)
    force_password_reset = db.Column(db.Boolean, nullable=False, default=False)
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)
    last_failed_login_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    users = db.relationship('User', backref='branch', lazy=True)
    stocks = db.relationship('ProductStock', backref='branch', lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    barcode = db.Column(db.String(120), unique=True, nullable=False)  # SKU / barcode
    price = db.Column(db.Float, nullable=False, default=0.0)
    currency = db.Column(db.String(12), nullable=False, default='USD')
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    stocks = db.relationship('ProductStock', backref='product', lazy=True)


class ProductStock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    threshold = db.Column(db.Integer, nullable=False, default=5)  # low-stock threshold
    location = db.Column(db.String(120), nullable=True)


class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), unique=True, nullable=False)
    contact_name = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(64), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(250), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy=True)


class PurchaseOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(40), nullable=False, default='pending')
    delivered_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('PurchaseOrderItem', backref='order', lazy=True)


class PurchaseOrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Float, nullable=False, default=0.0)


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Float, nullable=False, default=0.0)
    discount = db.Column(db.Float, nullable=False, default=0.0)
    payment_method = db.Column(db.String(32), nullable=False, default='cash')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('SaleItem', backref='sale', lazy=True)


class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # snapshot price


class ReturnTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    original_sale_id = db.Column(db.Integer, nullable=True)
    return_type = db.Column(db.String(32), nullable=False)
    payment_method = db.Column(db.String(32), nullable=False, default='cash')
    net_amount = db.Column(db.Float, nullable=False, default=0.0)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('ReturnItem', backref='return_transaction', lazy=True)


class ReturnItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    return_transaction_id = db.Column(db.Integer, db.ForeignKey('return_transaction.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    is_replacement = db.Column(db.Boolean, nullable=False, default=False)
    price = db.Column(db.Float, nullable=False, default=0.0)


# -----------------------------
# Utility: role-based access decorator
# -----------------------------

def api_error(message, status=400):
    return jsonify({'msg': message}), status


def validate_password(password):
    if not password or len(password) < 10:
        return 'Password must be at least 10 characters long.'
    if not any(c.isupper() for c in password):
        return 'Password must include at least one uppercase letter.'
    if not any(c.islower() for c in password):
        return 'Password must include at least one lowercase letter.'
    if not any(c.isdigit() for c in password):
        return 'Password must include at least one number.'
    if not any(c in '!@#$%^&*()-_=+[]{}|;:,.<>/?' for c in password):
        return 'Password must include at least one symbol.'
    return None


def generate_temporary_password(length=14):
    import secrets, string
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*()-_=+[]{}|;:,.<>?'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def ensure_user_profile_columns():
    if 'sqlite' not in app.config['SQLALCHEMY_DATABASE_URI']:
        return
    with app.app_context():
        with db.engine.connect() as conn:
            existing = [row[1] for row in conn.execute(text("PRAGMA table_info(user)")).all()]
            if 'full_name' not in existing:
                conn.execute(text("ALTER TABLE user ADD COLUMN full_name VARCHAR(120)"))
            if 'sex' not in existing:
                conn.execute(text("ALTER TABLE user ADD COLUMN sex VARCHAR(16)"))
            if 'age' not in existing:
                conn.execute(text("ALTER TABLE user ADD COLUMN age INTEGER"))
            conn.commit()


def ensure_stock_schema():
    if 'sqlite' not in app.config['SQLALCHEMY_DATABASE_URI']:
        return
    with app.app_context():
        with db.engine.connect() as conn:
            existing = [row[1] for row in conn.execute(text("PRAGMA table_info(product_stock)")).all()]
            if 'location' not in existing:
                conn.execute(text("ALTER TABLE product_stock ADD COLUMN location VARCHAR(120)"))
            conn.commit()


def ensure_sales_schema():
    if 'sqlite' not in app.config['SQLALCHEMY_DATABASE_URI']:
        return
    with app.app_context():
        with db.engine.connect() as conn:
            existing = [row[1] for row in conn.execute(text("PRAGMA table_info(sale)")).all()]
            if 'discount' not in existing:
                conn.execute(text("ALTER TABLE sale ADD COLUMN discount FLOAT DEFAULT 0.0"))
            if 'payment_method' not in existing:
                conn.execute(text("ALTER TABLE sale ADD COLUMN payment_method VARCHAR(32) DEFAULT 'cash'"))
            conn.commit()


def get_current_user():
    claims = get_jwt()
    username = claims.get('sub')
    return User.query.filter_by(username=username).first()


def auth_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return api_error('Authentication required.', 401)
        if user.locked:
            return api_error('This account is locked. Contact a manager or administrator.', 403)
        if user.force_password_reset and fn.__name__ != 'change_password':
            return api_error('Temporary password must be changed before using the system.', 403)
        return fn(*args, **kwargs)

    return wrapper


def role_required(allowed_roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            role = claims.get('role')
            if role == 'admin':
                return fn(*args, **kwargs)
            if role not in allowed_roles:
                return api_error('Insufficient privileges for this action.', 403)
            user = get_current_user()
            if user and user.locked:
                return api_error('This account is locked. Contact a manager or administrator.', 403)
            if user and user.force_password_reset and fn.__name__ != 'change_password':
                return api_error('Temporary password must be changed before using the system.', 403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


# -----------------------------
# Auth endpoints: signup, login
# - Signup restricted to manager role via a query param for bootstrapping convenience.
# -----------------------------


@app.route('/api/signup', methods=['POST'])
@role_required(['manager', 'admin'])
def signup():
    """Create a user. Only managers can create new accounts.
    JSON: {username, password, role, branch_id (optional)}
    Returns: user info (no password)
    """
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'cashier')
    full_name = data.get('full_name')
    sex = data.get('sex')
    age = data.get('age')
    branch_id = data.get('branch_id')
    branch_name = data.get('branch_name')
    manager = get_current_user()

    if not username:
        return api_error('Please enter a username.', 400)

    if role not in ['cashier', 'supervisor', 'manager']:
        return api_error('Invalid role. Only cashier, supervisor, and manager may be assigned.', 400)

    if manager.role != 'admin':
        if branch_id is None and not branch_name:
            branch_id = manager.branch_id
        elif branch_name and branch_name.strip() != (manager.branch.name if manager.branch else None):
            return api_error('Managers may only create users for their own branch.', 403)
        elif branch_id is not None:
            try:
                branch_id = int(branch_id)
            except (TypeError, ValueError):
                return api_error('branch_id must be a valid number.', 400)
            if branch_id != manager.branch_id:
                return api_error('You may only create users for your own branch.', 403)
        else:
            branch_id = manager.branch_id
    else:
        # Admins may create users for an existing or new branch, but non-admin users still require branch context.
        if branch_id is not None:
            try:
                branch_id = int(branch_id)
            except (TypeError, ValueError):
                return api_error('branch_id must be a valid number.', 400)
            if not Branch.query.get(branch_id):
                return api_error(f'Branch with id {branch_id} does not exist.', 404)
        elif branch_name:
            branch_name = branch_name.strip()
            if not branch_name:
                return api_error('branch_name cannot be empty.', 400)
            existing_branch = Branch.query.filter_by(name=branch_name).first()
            if existing_branch:
                branch_id = existing_branch.id
            else:
                new_branch = Branch(name=branch_name)
                db.session.add(new_branch)
                db.session.flush()
                branch_id = new_branch.id
        elif role != 'admin':
            return api_error('branch_id or branch_name is required when creating non-admin users.', 400)

    if age is not None:
        try:
            age = int(age)
            if age < 0:
                return api_error('Age must be a non-negative number.', 400)
        except (TypeError, ValueError):
            return api_error('Age must be a valid number.', 400)

    if User.query.filter_by(username=username).first():
        return api_error(f'The username "{username}" is already taken.', 400)

    generated_password = False
    if not password:
        password = generate_temporary_password()
        generated_password = True

    password_error = validate_password(password)
    if password_error:
        return api_error(password_error, 400)

    user = User(username=username, role=role, sex=sex, age=age, branch_id=branch_id, force_password_reset=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    response = {'id': user.id, 'username': user.username, 'role': user.role, 'force_password_reset': user.force_password_reset}
    if generated_password:
        response['temp_password'] = password
    return jsonify(response), 201


@app.route('/api/login', methods=['POST'])
def login():
    """Authenticate a user and return JWT access token.
    JSON: {username, password}
    Returns: {access_token}
    """
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'msg': 'username and password required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        if user:
            user.failed_login_attempts += 1
            user.last_failed_login_at = datetime.utcnow()
            if user.failed_login_attempts >= app.config['MAX_FAILED_LOGIN_ATTEMPTS']:
                user.locked = True
            db.session.commit()
        return api_error('Invalid username or password. Please try again.', 401)

    if user.locked:
        return api_error('This account is locked. Contact a manager or administrator.', 403)

    if user.failed_login_attempts > 0:
        user.failed_login_attempts = 0
        user.last_failed_login_at = None
        db.session.commit()

    additional_claims = {"role": user.role, "user_id": user.id}
    access_token = create_access_token(identity=user.username, additional_claims=additional_claims)
    response = {
        'access_token': access_token,
        'role': user.role,
        'user_id': user.id,
        'force_password_reset': user.force_password_reset,
    }
    return jsonify(response), 200


# -----------------------------
# Branch management
# -----------------------------


@app.route('/api/branches', methods=['GET'])
@auth_required
def list_branches():
    user = get_current_user()
    if user.role == 'admin':
        branches = Branch.query.all()
    else:
        branches = Branch.query.filter_by(id=user.branch_id).all() if user.branch_id else []
    return jsonify([{'id': b.id, 'name': b.name, 'address': b.address} for b in branches])


@app.route('/api/branches', methods=['POST'])
@role_required(['manager'])
def create_branch():
    data = request.get_json() or {}
    name = data.get('name')
    address = data.get('address')
    if not name:
        return api_error('Branch name is required and cannot be empty.', 400)
    branch = Branch(name=name, address=address)
    db.session.add(branch)
    db.session.commit()
    return jsonify({'id': branch.id, 'name': branch.name}), 201


# -----------------------------
# Product CRUD + stock endpoints
# -----------------------------


@app.route('/api/products', methods=['GET'])
@auth_required
def list_products():
    # Optional query params: branch_id to include stock levels or barcode to find by barcode
    user = get_current_user()
    branch_id = request.args.get('branch_id', type=int)
    barcode = request.args.get('barcode')
    if branch_id and user.role != 'admin' and user.branch_id != branch_id:
        return api_error('You may only view stock for your own branch.', 403)
    if barcode:
        p = Product.query.filter_by(barcode=barcode).first()
        if not p:
            return api_error('Product not found.', 404)
        item = {'id': p.id, 'name': p.name, 'barcode': p.barcode, 'price': p.price, 'currency': p.currency, 'description': p.description}
        if branch_id:
            stock = ProductStock.query.filter_by(product_id=p.id, branch_id=branch_id).first()
            item['stock'] = stock.quantity if stock else 0
            item['threshold'] = stock.threshold if stock else None
        return jsonify(item)

    products = Product.query.all()
    out = []
    for p in products:
        item = {'id': p.id, 'name': p.name, 'barcode': p.barcode, 'price': p.price, 'currency': p.currency, 'description': p.description}
        if branch_id:
            stock = ProductStock.query.filter_by(product_id=p.id, branch_id=branch_id).first()
            item['stock'] = stock.quantity if stock else 0
            item['threshold'] = stock.threshold if stock else None
        out.append(item)
    return jsonify(out)


@app.route('/api/products', methods=['POST'])
@role_required(['supervisor', 'manager'])
def create_product():
    data = request.get_json() or {}
    name = data.get('name')
    barcode = data.get('barcode')
    price = data.get('price', 0.0)
    desc = data.get('description')
    if not name or not barcode:
        return api_error('Product name and barcode are required to save a product.', 400)
    if Product.query.filter_by(barcode=barcode).first():
        return api_error(f'A product with barcode "{barcode}" already exists.', 400)
    currency = data.get('currency', 'USD').upper()
    supported = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY']
    if currency not in supported:
        return api_error('Currency must be one of: ' + ', '.join(supported), 400)
    p = Product(name=name, barcode=barcode, price=price, currency=currency, description=desc)
    db.session.add(p)
    db.session.commit()
    return jsonify({'id': p.id, 'name': p.name, 'currency': p.currency}), 201


@app.route('/api/suppliers', methods=['GET'])
@role_required(['manager'])
def list_suppliers():
    suppliers = Supplier.query.order_by(Supplier.name).all()
    return jsonify([
        {
            'id': s.id,
            'name': s.name,
            'contact_name': s.contact_name,
            'phone': s.phone,
            'email': s.email,
            'address': s.address,
            'created_at': s.created_at.isoformat()
        }
        for s in suppliers
    ])


@app.route('/api/suppliers', methods=['POST'])
@role_required(['manager'])
def create_supplier():
    data = request.get_json() or {}
    name = data.get('name')
    if not name:
        return api_error('Supplier name is required.', 400)
    if Supplier.query.filter_by(name=name).first():
        return api_error(f'A supplier named "{name}" already exists.', 400)
    supplier = Supplier(
        name=name,
        contact_name=data.get('contact_name'),
        phone=data.get('phone'),
        email=data.get('email'),
        address=data.get('address')
    )
    db.session.add(supplier)
    db.session.commit()
    return jsonify({'id': supplier.id, 'name': supplier.name}), 201


@app.route('/api/suppliers/<int:supplier_id>', methods=['PUT'])
@role_required(['manager'])
def update_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    data = request.get_json() or {}
    supplier.name = data.get('name', supplier.name)
    supplier.contact_name = data.get('contact_name', supplier.contact_name)
    supplier.phone = data.get('phone', supplier.phone)
    supplier.email = data.get('email', supplier.email)
    supplier.address = data.get('address', supplier.address)
    db.session.commit()
    return jsonify({'id': supplier.id, 'name': supplier.name})


@app.route('/api/suppliers/<int:supplier_id>', methods=['DELETE'])
@role_required(['manager'])
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    db.session.delete(supplier)
    db.session.commit()
    return jsonify({'msg': 'Supplier deleted successfully.'})


@app.route('/api/purchase-orders', methods=['GET'])
@role_required(['supervisor', 'manager'])
def list_purchase_orders():
    supplier_id = request.args.get('supplier_id', type=int)
    branch_id = request.args.get('branch_id', type=int)
    query = PurchaseOrder.query
    if supplier_id:
        query = query.filter_by(supplier_id=supplier_id)
    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    orders = query.order_by(PurchaseOrder.created_at.desc()).all()
    return jsonify([
        {
            'id': o.id,
            'supplier_id': o.supplier_id,
            'supplier_name': o.supplier.name,
            'branch_id': o.branch_id,
            'status': o.status,
            'expected_date': o.expected_date.isoformat() if o.expected_date else None,
            'delivered_at': o.delivered_at.isoformat() if o.delivered_at else None,
            'order_date': o.order_date.isoformat(),
            'total_items': sum(item.quantity for item in o.items),
            'items': [
                {'product_id': item.product_id, 'quantity': item.quantity, 'price': item.price}
                for item in o.items
            ]
        }
        for o in orders
    ])


@app.route('/api/purchase-orders', methods=['POST'])
@role_required(['manager'])
def create_purchase_order():
    data = request.get_json() or {}
    supplier_id = data.get('supplier_id')
    branch_id = data.get('branch_id')
    expected_date = data.get('expected_date')
    items = data.get('items', [])
    if not supplier_id or not branch_id or not items:
        return api_error('supplier_id, branch_id, and at least one order item are required.', 400)
    supplier = Supplier.query.get(supplier_id)
    if not supplier:
        return api_error('Supplier not found.', 404)
    try:
        branch_id = int(branch_id)
    except (TypeError, ValueError):
        return api_error('branch_id must be a valid number.', 400)
    order = PurchaseOrder(supplier_id=supplier_id, branch_id=branch_id)
    if expected_date:
        try:
            order.expected_date = datetime.fromisoformat(expected_date)
        except ValueError:
            return api_error('expected_date must be in ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS', 400)
    for index, item in enumerate(items, start=1):
        pid = item.get('product_id')
        qty = item.get('quantity')
        price = item.get('price')
        if not pid or qty is None or price is None:
            return api_error(f'Order item {index} requires product_id, quantity, and price.', 400)
        try:
            pid = int(pid)
            qty = int(qty)
            price = float(price)
        except (TypeError, ValueError):
            return api_error(f'Order item {index} contains invalid numeric values.', 400)
        if qty <= 0 or price < 0:
            return api_error(f'Order item {index} quantity and price must be non-negative.', 400)
        product = Product.query.get(pid)
        if not product:
            return api_error(f'Product with ID {pid} not found.', 404)
        order.items.append(PurchaseOrderItem(product_id=pid, quantity=qty, price=price))
    db.session.add(order)
    db.session.commit()
    return jsonify({'id': order.id, 'status': order.status}), 201


@app.route('/api/purchase-orders/<int:order_id>/receive', methods=['POST'])
@role_required(['supervisor', 'manager'])
def receive_purchase_order(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    if order.status != 'pending':
        return api_error('Only pending purchase orders can be marked as delivered.', 400)
    order.status = 'delivered'
    order.delivered_at = datetime.utcnow()
    for item in order.items:
        stock = ProductStock.query.filter_by(product_id=item.product_id, branch_id=order.branch_id).first()
        if stock:
            stock.quantity += item.quantity
        else:
            stock = ProductStock(product_id=item.product_id, branch_id=order.branch_id, quantity=item.quantity, threshold=5)
            db.session.add(stock)
    db.session.commit()
    return jsonify({'id': order.id, 'status': order.status, 'delivered_at': order.delivered_at.isoformat()})


@app.route('/api/users', methods=['GET'])
@role_required(['manager'])
def list_users():
    user = get_current_user()
    if user.role == 'admin':
        users = User.query.order_by(User.created_at.desc()).all()
    else:
        users = User.query.filter_by(branch_id=user.branch_id).order_by(User.created_at.desc()).all()
    return jsonify([
        {
            'id': u.id,
            'username': u.username,
            'full_name': u.full_name,
            'role': u.role,
            'sex': u.sex,
            'age': u.age,
            'branch_id': u.branch_id,
            'locked': u.locked,
            'force_password_reset': u.force_password_reset,
            'created_at': u.created_at.isoformat()
        }
        for u in users
    ])


@app.route('/api/users/<int:user_id>/lock', methods=['POST'])
@role_required(['manager'])
def set_user_lock(user_id):
    data = request.get_json() or {}
    if 'locked' not in data:
        return api_error('locked field is required.', 400)
    user = User.query.get_or_404(user_id)
    manager = get_current_user()
    if user.role == 'admin':
        return api_error('Administrator accounts cannot be locked through this interface.', 403)
    if manager.role != 'admin' and user.branch_id != manager.branch_id:
        return api_error('You may only lock users from your own branch.', 403)
    user.locked = bool(data.get('locked'))
    db.session.commit()
    return jsonify({'id': user.id, 'username': user.username, 'locked': user.locked})


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@role_required(['admin'])
def delete_user(user_id):
    admin = get_current_user()
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        return api_error('Administrator accounts cannot be deleted through this interface.', 403)
    if user.id == admin.id:
        return api_error('You cannot delete your own account.', 403)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'msg': 'User deleted successfully.'})


@app.route('/api/users/<int:user_id>/password', methods=['POST'])
@role_required(['manager', 'admin'])
def reset_user_password(user_id):
    data = request.get_json() or {}
    password = data.get('password')
    if not password:
        # For admin-initiated resets, if no password supplied, generate a temporary one
        requester = get_current_user()
        if requester.role != 'admin':
            return api_error('New password is required to reset user password.', 400)
        password = generate_temporary_password()

    password_error = validate_password(password)
    if password_error:
        return api_error(password_error, 400)
    user = User.query.get_or_404(user_id)
    manager = get_current_user()
    # managers cannot reset admin passwords and can only act within their branch
    if manager.role != 'admin':
        if user.role == 'admin':
            return api_error('Administrator passwords cannot be reset through this interface.', 403)
        if user.branch_id != manager.branch_id:
            return api_error('You may only reset passwords for users in your own branch.', 403)
    # admin may reset any user's password
    user.set_password(password)
    user.force_password_reset = True
    user.failed_login_attempts = 0
    user.locked = False
    db.session.commit()
    resp = {'id': user.id, 'username': user.username, 'force_password_reset': user.force_password_reset}
    if manager.role == 'admin' and not data.get('password'):
        resp['temp_password'] = password
    return jsonify(resp)


@app.route('/api/change-password', methods=['POST'])
@jwt_required()
def change_password():
    data = request.get_json() or {}
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    if not old_password or not new_password:
        return api_error('Both current and new password are required.', 400)
    user = get_current_user()
    if user is None or not user.check_password(old_password):
        return api_error('Current password is incorrect.', 403)
    password_error = validate_password(new_password)
    if password_error:
        return api_error(password_error, 400)
    user.set_password(new_password)
    user.force_password_reset = False
    user.failed_login_attempts = 0
    user.locked = False
    db.session.commit()
    return jsonify({'msg': 'Password updated successfully.'}), 200


@app.route('/api/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt().get('jti')
    if jti:
        revoked = RevokedToken(jti=jti)
        db.session.add(revoked)
        db.session.commit()
    return jsonify({'msg': 'Logged out successfully.'}), 200


@app.route('/api/products/<int:product_id>', methods=['PUT'])
@role_required(['supervisor', 'manager'])
def update_product(product_id):
    p = Product.query.get_or_404(product_id)
    data = request.get_json() or {}
    p.name = data.get('name', p.name)
    p.price = data.get('price', p.price)
    p.description = data.get('description', p.description)
    db.session.commit()
    return jsonify({'id': p.id, 'name': p.name})


@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@role_required(['manager'])
def delete_product(product_id):
    p = Product.query.get_or_404(product_id)
    db.session.delete(p)
    db.session.commit()
    return jsonify({'msg': 'deleted'})


@app.route('/api/stocks', methods=['GET'])
@auth_required
def list_stocks():
    user = get_current_user()
    branch_id = request.args.get('branch_id', type=int)
    product_id = request.args.get('product_id', type=int)
    query = ProductStock.query
    if user.role != 'admin':
        branch_id = user.branch_id
    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    if product_id:
        query = query.filter_by(product_id=product_id)
    stocks = query.all()
    return jsonify([
        {
            'id': s.id,
            'product_id': s.product_id,
            'product_name': s.product.name,
            'barcode': s.product.barcode,
            'branch_id': s.branch_id,
            'quantity': s.quantity,
            'threshold': s.threshold,
            'location': s.location,
        }
        for s in stocks
    ])


@app.route('/api/stocks', methods=['POST'])
@role_required(['supervisor', 'manager'])
def set_stock():
    """Set or update stock for a product at a branch.
    JSON: {product_id, branch_id, quantity, threshold, location}
    """
    user = get_current_user()
    data = request.get_json() or {}
    product_id = data.get('product_id')
    branch_id = data.get('branch_id')
    quantity = data.get('quantity', 0)
    threshold = data.get('threshold', 5)
    location = data.get('location')
    if not product_id or not branch_id:
        return api_error('Please provide both product_id and branch_id to update stock.', 400)
    if user.role != 'admin' and user.branch_id != int(branch_id):
        return api_error('You may only update stock for your own branch.', 403)
    try:
        product_id = int(product_id)
        branch_id = int(branch_id)
        quantity = int(quantity)
        threshold = int(threshold)
    except (TypeError, ValueError):
        return api_error('Stock values must be valid numbers.', 400)
    if quantity < 0:
        return api_error('Stock quantity cannot be negative.', 400)
    if threshold < 0:
        return api_error('Stock threshold cannot be negative.', 400)
    stock = ProductStock.query.filter_by(product_id=product_id, branch_id=branch_id).first()
    if not stock:
        stock = ProductStock(product_id=product_id, branch_id=branch_id, quantity=quantity, threshold=threshold, location=location)
        db.session.add(stock)
    else:
        stock.quantity = quantity
        stock.threshold = threshold
        stock.location = location
    db.session.commit()
    return jsonify({'msg': 'ok'})


# -----------------------------
# Sales endpoints: create sale, which decrements stock and stores sale items
# -----------------------------


@app.route('/api/sales', methods=['POST'])
@role_required(['cashier', 'supervisor', 'manager'])
def create_sale():
    """Create a sale and decrement stock.
    JSON: {branch_id, items: [{product_id, quantity}], payment_method, discount}
    """
    user = get_current_user()
    claims = get_jwt()
    user_id = claims.get('user_id')
    data = request.get_json() or {}
    branch_id = data.get('branch_id')
    items = data.get('items', [])
    payment_method = (data.get('payment_method') or 'cash').lower()
    discount = data.get('discount', 0.0)
    valid_payments = ['cash', 'card', 'ecocash']
    if not branch_id or not items:
        return api_error('Branch ID and at least one sale item are required.', 400)
    if payment_method not in valid_payments:
        return api_error(f'Payment method must be one of: {", ".join(valid_payments)}.', 400)
    try:
        branch_id = int(branch_id)
    except (TypeError, ValueError):
        return api_error('Branch ID must be a valid number.', 400)
    if user.role != 'admin' and user.branch_id != branch_id:
        return api_error('You may only record sales for your own branch.', 403)
    try:
        discount = float(discount)
    except (TypeError, ValueError):
        return api_error('Discount must be a valid number.', 400)
    if discount < 0:
        return api_error('Discount cannot be negative.', 400)

    sale = Sale(branch_id=branch_id, user_id=user_id, total=0.0, payment_method=payment_method, discount=discount)
    subtotal = 0.0
    for index, it in enumerate(items, start=1):
        pid = it.get('product_id')
        qty = it.get('quantity')
        if pid is None:
            return api_error(f'Item {index} is missing a product_id.', 400)
        try:
            pid = int(pid)
            qty = int(qty)
        except (TypeError, ValueError):
            return api_error(f'Item {index} requires valid numeric product_id and quantity.', 400)
        if qty <= 0:
            return api_error(f'Item {index} quantity must be at least 1.', 400)
        product = Product.query.get(pid)
        if not product:
            return api_error(f'Product with ID {pid} not found.', 404)
        stock = ProductStock.query.filter_by(product_id=pid, branch_id=branch_id).first()
        if not stock:
            return api_error(f'No stock record found for product {product.name} at branch {branch_id}.', 400)
        if stock.quantity < qty:
            return api_error(f'Insufficient stock for product {product.name}.', 400)
        # decrement
        stock.quantity -= qty
        line_total = product.price * qty
        subtotal += line_total
        sale_item = SaleItem(product_id=pid, quantity=qty, price=product.price)
        sale.items.append(sale_item)

    total = max(0.0, subtotal - discount)
    sale.total = total
    db.session.add(sale)
    db.session.commit()

    # After committing, check for low-stock items
    low = ProductStock.query.filter_by(branch_id=branch_id).filter(ProductStock.quantity <= ProductStock.threshold).all()
    alerts = [{'product_id': s.product_id, 'qty': s.quantity, 'threshold': s.threshold} for s in low]
    return jsonify({'sale_id': sale.id, 'subtotal': subtotal, 'discount': discount, 'total': total, 'payment_method': payment_method, 'low_stock_alerts': alerts}), 201


@app.route('/api/returns', methods=['POST'])
@role_required(['cashier', 'supervisor', 'manager'])
def process_return():
    """Process a return, exchange, or damaged goods record.
    JSON: {branch_id, return_type, payment_method, items: [{product_id, quantity}], replacement_items?: [{product_id, quantity}], original_sale_id?, notes?}
    """
    user = get_current_user()
    data = request.get_json() or {}
    branch_id = data.get('branch_id')
    return_type = (data.get('return_type') or '').lower()
    payment_method = (data.get('payment_method') or 'cash').lower()
    items = data.get('items', [])
    replacement_items = data.get('replacement_items', [])
    original_sale_id = data.get('original_sale_id')
    notes = data.get('notes')

    valid_types = ['refund', 'exchange', 'damaged']
    valid_payments = ['cash', 'card', 'ecocash']
    if not branch_id or not items:
        return api_error('Branch ID and at least one return item are required.', 400)
    if return_type not in valid_types:
        return api_error(f'Return type must be one of: {", ".join(valid_types)}.', 400)
    if payment_method not in valid_payments:
        return api_error(f'Payment method must be one of: {", ".join(valid_payments)}.', 400)
    try:
        branch_id = int(branch_id)
    except (TypeError, ValueError):
        return api_error('Branch ID must be a valid number.', 400)
    if user.role != 'admin' and user.branch_id != branch_id:
        return api_error('You may only process returns for your own branch.', 403)
    if replacement_items and return_type != 'exchange':
        return api_error('Replacement items are only allowed for exchanges.', 400)

    total_return = 0.0
    total_replacement = 0.0
    return_tx = ReturnTransaction(
        branch_id=branch_id,
        user_id=user.id,
        original_sale_id=original_sale_id,
        return_type=return_type,
        payment_method=payment_method,
        notes=notes,
    )

    for index, it in enumerate(items, start=1):
        pid = it.get('product_id')
        qty = it.get('quantity')
        if pid is None:
            return api_error(f'Return item {index} is missing a product_id.', 400)
        try:
            pid = int(pid)
            qty = int(qty)
        except (TypeError, ValueError):
            return api_error(f'Return item {index} requires valid numeric product_id and quantity.', 400)
        if qty <= 0:
            return api_error(f'Return item {index} quantity must be at least 1.', 400)
        product = Product.query.get(pid)
        if not product:
            return api_error(f'Product with ID {pid} not found.', 404)
        if return_type in ['refund', 'exchange']:
            stock = ProductStock.query.filter_by(product_id=pid, branch_id=branch_id).first()
            if stock:
                stock.quantity += qty
            else:
                stock = ProductStock(product_id=pid, branch_id=branch_id, quantity=qty, threshold=5)
                db.session.add(stock)
        return_tx.items.append(ReturnItem(product_id=pid, quantity=qty, is_replacement=False, price=product.price))
        total_return += product.price * qty

    for index, it in enumerate(replacement_items, start=1):
        pid = it.get('product_id')
        qty = it.get('quantity')
        if pid is None:
            return api_error(f'Replacement item {index} is missing a product_id.', 400)
        try:
            pid = int(pid)
            qty = int(qty)
        except (TypeError, ValueError):
            return api_error(f'Replacement item {index} requires valid numeric product_id and quantity.', 400)
        if qty <= 0:
            return api_error(f'Replacement item {index} quantity must be at least 1.', 400)
        product = Product.query.get(pid)
        if not product:
            return api_error(f'Product with ID {pid} not found.', 404)
        stock = ProductStock.query.filter_by(product_id=pid, branch_id=branch_id).first()
        if not stock or stock.quantity < qty:
            return api_error(f'Insufficient stock to replace product {product.name}.', 400)
        stock.quantity -= qty
        return_tx.items.append(ReturnItem(product_id=pid, quantity=qty, is_replacement=True, price=product.price))
        total_replacement += product.price * qty

    if return_type == 'refund':
        return_tx.net_amount = -total_return
    elif return_type == 'exchange':
        return_tx.net_amount = total_replacement - total_return
    else:
        return_tx.net_amount = 0.0

    db.session.add(return_tx)
    db.session.commit()

    return jsonify({
        'id': return_tx.id,
        'branch_id': branch_id,
        'return_type': return_type,
        'payment_method': payment_method,
        'net_amount': return_tx.net_amount,
        'returned_items': [{'product_id': item.product_id, 'quantity': item.quantity, 'price': item.price} for item in return_tx.items if not item.is_replacement],
        'replacement_items': [{'product_id': item.product_id, 'quantity': item.quantity, 'price': item.price} for item in return_tx.items if item.is_replacement],
        'notes': notes,
        'original_sale_id': original_sale_id,
    }), 201


# -----------------------------
# Reporting endpoints
# - /api/reports/sales?range=daily|weekly|monthly&branch_id=..
# Aggregates total sales for the given range and branch (optional)
# -----------------------------


@app.route('/api/reports/sales')
@role_required(['supervisor', 'manager'])
def sales_report():
    user = get_current_user()
    r = request.args.get('range', 'daily')
    branch_id = request.args.get('branch_id', type=int)
    if user.role != 'admin':
        branch_id = user.branch_id
    if branch_id is None:
        return api_error('Branch ID is required for this report.', 400)
    now = datetime.utcnow()
    if r == 'daily':
        start = datetime(now.year, now.month, now.day)
    elif r == 'weekly':
        start = now - timedelta(days=now.weekday())
        start = datetime(start.year, start.month, start.day)
    elif r == 'monthly':
        start = datetime(now.year, now.month, 1)
    else:
        return api_error('Invalid report range selected. Choose daily, weekly, or monthly.', 400)

    q = Sale.query.filter(Sale.created_at >= start)
    if branch_id:
        q = q.filter_by(branch_id=branch_id)
    sales = q.all()
    total = sum(s.total for s in sales)
    count = len(sales)
    return jsonify({'range': r, 'start': start.isoformat(), 'total': total, 'count': count})


# -----------------------------
# Alerts endpoint: returns low-stock products per branch
# -----------------------------


@app.route('/api/profile')
@auth_required
def profile():
    user = get_current_user()
    if user is None:
        return api_error('Authentication required.', 401)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'full_name': user.full_name,
        'role': user.role,
        'sex': user.sex,
        'age': user.age,
        'branch_id': user.branch_id,
        'locked': user.locked,
        'force_password_reset': user.force_password_reset,
        'created_at': user.created_at.isoformat()
    })


@app.route('/api/alerts')
@auth_required
def alerts():
    user = get_current_user()
    branch_id = request.args.get('branch_id', type=int)
    if user.role != 'admin':
        branch_id = user.branch_id
    q = ProductStock.query
    if branch_id:
        q = q.filter_by(branch_id=branch_id)
    low = q.filter(ProductStock.quantity <= ProductStock.threshold).all()
    out = []
    for s in low:
        out.append({'product_id': s.product_id, 'product_name': s.product.name, 'branch_id': s.branch_id, 'quantity': s.quantity, 'threshold': s.threshold})
    return jsonify(out)


# -----------------------------
# Utility routes: init DB and simple web UI
# -----------------------------


migration_done = False

@app.before_request
def maybe_migrate_user_schema():
    global migration_done
    if migration_done:
        return
    ensure_user_profile_columns()
    ensure_stock_schema()
    ensure_sales_schema()
    db.create_all()
    migration_done = True


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload.get('jti')
    if not jti:
        return True
    if RevokedToken.query.filter_by(jti=jti).first():
        return True
    user = User.query.filter_by(username=jwt_payload.get('sub')).first()
    return user is None or user.locked


@app.after_request
def set_secure_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net https://unpkg.com; style-src 'self' https://cdn.jsdelivr.net; connect-src 'self' https://cdn.jsdelivr.net https://unpkg.com; object-src 'none'; frame-ancestors 'none'; base-uri 'self';"
    return response


@app.errorhandler(404)
def handle_not_found(error):
    return api_error('The requested resource was not found.', 404)


@app.errorhandler(500)
def handle_internal_error(error):
    return api_error('An unexpected error occurred on the server. Please try again later.', 500)


@app.route('/init-db')
def init_db():
    if not app.config['ENABLE_DB_INIT']:
        return api_error('Database initialization is disabled.', 403)
    init_secret = request.args.get('init_key')
    if not init_secret or init_secret != app.config['DB_INIT_SECRET']:
        return api_error('Invalid initialization token.', 403)

    db.drop_all()
    db.create_all()
    b = Branch(name='Main Branch', address='HQ')
    db.session.add(b)
    db.session.commit()

    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    if not admin_password:
        return api_error('ADMIN_PASSWORD must be configured to create the admin account.', 500)

    admin = User(username=admin_username, role='admin', branch_id=b.id, force_password_reset=False)
    admin.set_password(admin_password)
    db.session.add(admin)
    db.session.commit()
    return jsonify({'msg': 'db initialized', 'admin': admin_username, 'branch_id': b.id})


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


# GUI pages
@app.route('/products')
def products_page():
    return render_template('products.html')


@app.route('/branches_page')
def branches_page():
    return render_template('branches.html')


@app.route('/stocks_page')
def stocks_page():
    return render_template('stocks.html')


@app.route('/suppliers')
def suppliers_page():
    return render_template('suppliers.html')


@app.route('/reports_page')
def reports_page():
    return render_template('reports.html')


@app.route('/employees_page')
def employees_page():
    return render_template('employees.html')


@app.route('/checkout')
def checkout():
    return render_template('checkout.html')


@app.route('/returns')
def returns_page():
    return render_template('returns.html')


@app.route('/profile')
def profile_page():
    return render_template('profile.html')


class RevokedToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(128), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=app.config['FLASK_DEBUG'])
