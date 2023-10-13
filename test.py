import unittest
from app import app, db 
from app import Product, User 

class APITestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@mysql_host/database_name'
        self.app = app.test_client()
        db.create_all()

        product = Product(sku='TEST123', name='Test Product', price=19, brand='Test Brand')
        db.session.add(product)

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_product(self):
        response = self.app.get('/products/1')
        self.assertEqual(response.status_code, 200)

    def test_get_nonexistent_product(self):
        response = self.app.get('/products/100')
        self.assertEqual(response.status_code, 404)

    def test_login(self):
        response = self.app.post('/login', json={'email': 'sebas@example.com', 'password': '12345'})
        self.assertEqual(response.status_code, 200)

    def test_login_invalid_credentials(self):
        response = self.app.post('/login', json={'email': 'bad_admin', 'password': 'bad'})
        self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
    unittest.main()
