import pytest
from datetime import datetime, timedelta
from app import app, db, Customer, Loan, Book

@pytest.fixture(scope='function')
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    with app.app_context():
        db.create_all()  # Create tables before each test

        yield app.test_client()  # Provide the test client

        db.session.remove()
        db.drop_all()  # Clean up after tests

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Welcome to the Library Management System!" in response.data

def test_add_customer(client):
    customer_data = {
        "name": "John Doe",
        "city": "Springfield",
        "age": 30,
        "email": "john@example.com"
    }
    
    response = client.post('/customers', json=customer_data)
    assert response.status_code == 201
    assert b"Customer added" in response.data

    with app.app_context():
        customer = Customer.query.filter_by(email="john@example.com").first()
        assert customer is not None
        assert customer.name == "John Doe"

def test_view_customers(client):
    customer_data = {
        "name": "Jane Doe",
        "city": "Metropolis",
        "age": 25,
        "email": "jane@example.com"
    }
    client.post('/customers', json=customer_data)

    response = client.get('/customers')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1  # Check that only one customer is returned
    assert data[0]['name'] == "Jane Doe"

def test_add_book(client):
    book_data = {
        "name": "To Kill a Mockingbird",
        "author": "Harper Lee",
        "year_published": 1960,
        "type": 1
    }
    
    response = client.post('/books', json=book_data)
    assert response.status_code == 201
    assert b"Book added" in response.data

    with app.app_context():
        book = Book.query.filter_by(name="To Kill a Mockingbird").first()
        assert book is not None
        assert book.author == "Harper Lee"

def test_view_late_loans(client):
    with app.app_context():
        # Create a customer
        customer = Customer(name="John Smith", city="Gotham", age=40, email="john.smith@example.com", is_active=True)
        db.session.add(customer)
        db.session.commit()

        # Create a book
        book = Book(name="1984", author="George Orwell", year_published=1949, type=1)
        db.session.add(book)
        db.session.commit()

        # Create a loan with a return date in the past (1 day ago)
        past_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        loan = Loan(cust_id=customer.id, book_id=book.id, loan_date="2023-09-01", return_date=past_date, is_active=True)
        db.session.add(loan)
        db.session.commit()

    # Call the endpoint to check for late loans
    response = client.get('/loans/late')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['customer_id'] == customer.id
    assert data[0]['book_id'] == book.id

def test_return_book(client):
    with app.app_context():
        customer = Customer(name="Alice Wonderland", city="Wonderland", age=28, email="alice@example.com", is_active=True)
        db.session.add(customer)
        db.session.commit()
        
        book = Book(name="The Great Gatsby", author="F. Scott Fitzgerald", year_published=1925, type=1)
        db.session.add(book)
        db.session.commit()
        
        loan = Loan(cust_id=customer.id, book_id=book.id, loan_date="2023-09-01", return_date=None, is_active=True)
        db.session.add(loan)
        db.session.commit()
    
    # Simulate returning the book
    with app.app_context():
        loan_to_return = Loan.query.first()
        loan_to_return.is_active = False
        loan_to_return.return_date = datetime.now().strftime('%Y-%m-%d')
        db.session.commit()
        
        assert loan_to_return.return_date is not None
        assert loan_to_return.is_active is False

# To run the tests, use the command: pytest -v
