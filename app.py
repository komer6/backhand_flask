import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize Flask application
app = Flask(__name__)

# Enable Cross-Origin Resource Sharing (if needed)
CORS(app)

# Configure SQLAlchemy Database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the SQLAlchemy object
db = SQLAlchemy(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Define models
class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    year_published = db.Column(db.Integer, nullable=False)
    type = db.Column(db.Integer, nullable=False)

class Loan(db.Model):
    __tablename__ = 'loans'
    id = db.Column(db.Integer, primary_key=True)
    cust_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    loan_date = db.Column(db.String(40), nullable=False)
    return_date = db.Column(db.String(40), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    # Define relationships
    customer = db.relationship('Customer', backref='loans')
    book = db.relationship('Book', backref='loans')

class Customer(db.Model):
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

# Create the database and tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    logger.info("Home page accessed.")
    return "Welcome to the Library Management System!"

@app.route('/customers', methods=['GET'])
def view_customers():
    logger.info("View all customers request.")
    customers = Customer.query.all()
    customers_list = [{
        "id": customer.id,
        "name": customer.name,
        "city": customer.city,
        "age": customer.age,
        "email": customer.email,
        "is_active": customer.is_active
    } for customer in customers]
    
    return jsonify(customers_list), 200

@app.route('/customers', methods=['POST'])
def add_customer():
    data = request.json
    logger.info(f"Adding a new customer: {data['name']}")
    new_customer = Customer(name=data['name'], city=data['city'], age=data['age'], email=data['email'])
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({"message": "Customer added"}), 201

from sqlalchemy.orm import joinedload

@app.route('/loans/late', methods=['GET'])
def view_late_loans():
    current_date = datetime.now().strftime('%Y-%m-%d')
    logger.info(f"Checking for late loans as of {current_date}.")
    late_loans = Loan.query.filter(Loan.return_date < current_date, Loan.is_active == True) \
        .options(joinedload(Loan.customer), joinedload(Loan.book)).all()

    late_loans_list = [{
        "loan_id": loan.id,
        "customer_id": loan.cust_id,
        "customer_name": loan.customer.name,
        "book_id": loan.book_id,
        "book_name": loan.book.name,
        "loan_date": loan.loan_date,
        "return_date": loan.return_date,
        "is_active": loan.is_active
    } for loan in late_loans]

    logger.info(f"Found {len(late_loans_list)} late loans.")
    return jsonify(late_loans_list), 200

@app.route('/books', methods=['POST'])
def add_book():
    data = request.json
    logger.info(f"Adding a new book: {data['name']}")
    new_book = Book(name=data['name'], author=data['author'], year_published=data['year_published'], type=data['type'])
    db.session.add(new_book)
    db.session.commit()
    return jsonify({"message": "Book added"}), 201

# Run the application
if __name__ == '__main__':
    logger.info("Starting the Flask app.")
    app.run(debug=True)
