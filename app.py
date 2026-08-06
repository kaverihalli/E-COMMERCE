import os
import re
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, 
    url_for, flash, session, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-ecommerce-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -----------------------------------------------------------------------------
# Database Models
# -----------------------------------------------------------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Buyer')  # Admin, Seller, Buyer
    phone = db.Column(db.String(15), nullable=True)
    address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship('Product', backref='seller', lazy=True)
    reviews = db.relationship('Review', backref='buyer', lazy=True)
    orders = db.relationship('Order', backref='buyer', lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    color = db.Column(db.String(50), nullable=False)
    size = db.Column(db.String(50), nullable=False)
    ratings = db.Column(db.Float, default=0.0)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    reviews = db.relationship('Review', backref='product', lazy=True, cascade="all, delete-orphan")


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    buyer_phone = db.Column(db.String(15), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# -----------------------------------------------------------------------------
# Database Verification & Initialization
# -----------------------------------------------------------------------------

def init_db():
    """Verifies database existence and seeds predefined Admin account."""
    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(email='admin@gmail.com').first()
        if not admin:
            admin_user = User(
                name='Super Admin',
                email='admin@gmail.com',
                password=generate_password_hash('admin'),
                role='Admin',
                phone='1234567890',
                address='Headquarters'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("[Database] Predefined Admin account initialized successfully.")
        else:
            print("[Database] Verification complete. Database and Admin exist.")

init_db()

# -----------------------------------------------------------------------------
# Authentication Helpers & Decorators
# -----------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session or session['user_role'] not in roles:
                flash("Unauthorized access for your user role.", "danger")
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# -----------------------------------------------------------------------------
# Validations
# -----------------------------------------------------------------------------

def validate_email(email):
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email)

def validate_phone(phone):
    return re.match(r"^\+?\d{10,15}$", phone)

# -----------------------------------------------------------------------------
# Core Routes
# -----------------------------------------------------------------------------

@app.route('/')
def home():
    products = Product.query.all()
    return render_template('home.html', products=products)

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/contact/', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not message:
            flash("All fields are required.", "danger")
        elif not validate_email(email):
            flash("Invalid email format.", "danger")
        else:
            flash("Thank you! Your message has been sent.", "success")
            return redirect(url_for('contact'))
            
    return render_template('contact.html')

@app.route('/dashboard/')
@login_required
@role_required('Admin')
def dashboard():
    total_users = User.query.count()
    total_sellers = User.query.filter_by(role='Seller').count()
    total_buyers = User.query.filter_by(role='Buyer').count()
    total_products = Product.query.count()
    total_orders = Order.query.count()

    analytics = {
        'total_users': total_users,
        'sellers': total_sellers,
        'buyers': total_buyers,
        'products': total_products,
        'orders': total_orders
    }
    return render_template('dashboard.html', analytics=analytics)

# -----------------------------------------------------------------------------
# Authentication Routes
# -----------------------------------------------------------------------------

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'Buyer')
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        if not name or not email or not password or not phone or not address:
            flash("All fields are required.", "danger")
            return render_template('user_auth/register.html')

        if not validate_email(email):
            flash("Please enter a valid email address.", "danger")
            return render_template('user_auth/register.html')

        if not validate_phone(phone):
            flash("Phone number must contain 10-15 digits.", "danger")
            return render_template('user_auth/register.html')

        if len(password) < 5:
            flash("Password must be at least 5 characters long.", "danger")
            return render_template('user_auth/register.html')

        if User.query.filter_by(email=email).first():
            flash("Email is already registered.", "warning")
            return render_template('user_auth/register.html')

        hashed_pwd = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_pwd, role=role, phone=phone, address=address)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('user_auth/register.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template('user_auth/login.html')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for('dashboard') if user.role == 'Admin' else url_for('home'))

        flash("Invalid email or password.", "danger")

    return render_template('user_auth/login.html')


@app.route('/logout/')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


@app.route('/profile/')
@login_required
def profile():
    user = User.query.get_or_404(session['user_id'])
    return render_template('user_auth/profile.html', user=user)


@app.route('/edit_profile/', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = User.query.get_or_404(session['user_id'])
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        if not name or not phone or not address:
            flash("All fields are required.", "danger")
        elif not validate_phone(phone):
            flash("Invalid phone number format.", "danger")
        else:
            user.name = name
            user.phone = phone
            user.address = address
            session['user_name'] = name
            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for('profile'))

    return render_template('user_auth/edit_profile.html', user=user)

# -----------------------------------------------------------------------------
# Product CRUD Routes (Seller / Admin)
# -----------------------------------------------------------------------------

@app.route('/product/read/')
def product_read():
    products = Product.query.all()
    return render_template('product/product_read.html', products=products)


@app.route('/product/add/', methods=['GET', 'POST'])
@login_required
@role_required('Seller', 'Admin')
def product_add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        price = request.form.get('price', '').strip()
        description = request.form.get('description', '').strip()
        color = request.form.get('color', '').strip()
        size = request.form.get('size', '').strip()

        if not all([name, price, description, color, size]):
            flash("All product fields are required.", "danger")
            return render_template('product/product_add.html')

        try:
            price_val = float(price)
            if price_val <= 0:
                raise ValueError()
        except ValueError:
            flash("Price must be a positive number.", "danger")
            return render_template('product/product_add.html')

        product = Product(
            name=name, price=price_val, description=description,
            color=color, size=size, ratings=0.0, seller_id=session['user_id']
        )
        db.session.add(product)
        db.session.commit()

        flash("Product added successfully!", "success")
        return redirect(url_for('product_read'))

    return render_template('product/product_add.html')


@app.route('/product/edit/<int:product_id>/', methods=['GET', 'POST'])
@login_required
@role_required('Seller', 'Admin')
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)

    if session['user_role'] != 'Admin' and product.seller_id != session['user_id']:
        flash("Unauthorized to edit this product.", "danger")
        return redirect(url_for('product_read'))

    if request.method == 'POST':
        product.name = request.form.get('name', '').strip()
        product.description = request.form.get('description', '').strip()
        product.color = request.form.get('color', '').strip()
        product.size = request.form.get('size', '').strip()
        
        try:
            price = float(request.form.get('price', 0))
            if price <= 0:
                raise ValueError()
            product.price = price
        except ValueError:
            flash("Invalid price value.", "danger")
            return render_template('product/product_edit.html', product=product)

        db.session.commit()
        flash("Product updated successfully!", "success")
        return redirect(url_for('product_read'))

    return render_template('product/product_edit.html', product=product)


@app.route('/product/delete/<int:product_id>/', methods=['GET', 'POST'])
@login_required
@role_required('Seller', 'Admin')
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)

    if session['user_role'] != 'Admin' and product.seller_id != session['user_id']:
        flash("Unauthorized to delete this product.", "danger")
        return redirect(url_for('product_read'))

    if request.method == 'POST':
        db.session.delete(product)
        db.session.commit()
        flash("Product deleted successfully!", "success")
        return redirect(url_for('product_read'))

    return render_template('product/product_delete.html', product=product)

# -----------------------------------------------------------------------------
# Reviews & Chatbot Analytics API
# -----------------------------------------------------------------------------

@app.route('/product/<int:product_id>/review/', methods=['POST'])
@login_required
@role_required('Buyer')
def add_review(product_id):
    rating = request.form.get('rating')
    comment = request.form.get('comment', '').strip()

    if not rating or not comment:
        flash("Rating and comment are required.", "danger")
        return redirect(url_for('product_read'))

    review = Review(
        product_id=product_id,
        buyer_id=session['user_id'],
        rating=int(rating),
        comment=comment
    )
    db.session.add(review)

    # Recalculate rating
    all_reviews = Review.query.filter_by(product_id=product_id).all()
    total_ratings = sum([r.rating for r in all_reviews]) + int(rating)
    product = Product.query.get(product_id)
    product.ratings = round(total_ratings / (len(all_reviews) + 1), 1)

    db.session.commit()
    flash("Review added successfully!", "success")
    return redirect(url_for('product_read'))


@app.route('/api/chatbot/analytics/', methods=['GET'])
def chatbot_analytics():
    option = request.args.get('option', '')
    if option == 'users':
        count = User.query.count()
        sellers = User.query.filter_by(role='Seller').count()
        buyers = User.query.filter_by(role='Buyer').count()
        res = f"Total Registered Users: {count} (Sellers: {sellers}, Buyers: {buyers})"
    elif option == 'products':
        count = Product.query.count()
        res = f"Total Active Products in Store: {count}"
    elif option == 'orders':
        count = Order.query.count()
        res = f"Total Orders Placed: {count}"
    elif option == 'top_product':
        p = Product.query.order_by(Product.ratings.desc()).first()
        res = f"Highest Rated Product: {p.name} ({p.ratings} Stars)" if p else "No products found."
    else:
        res = "Please select a valid option from the chatbot menu."

    return jsonify({'response': res})

if __name__ == '__main__':
    app.run(debug=True)