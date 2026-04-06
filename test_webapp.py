import requests
import os
from flask import Flask
from webapp import app as flask_app

# Test the AI Test Runner functionality
def test_ai_test_runner():
    with flask_app.test_client() as client:
        # First, login
        login_response = client.post('/login', data={
            'employee_id': 'test123',
            'password': 'password'
        }, follow_redirects=True)

        print(f"Login status: {login_response.status_code}")

        if login_response.status_code == 200:
            print("Login successful")

            # Check if we can access the index page
            index_response = client.get('/')
            print(f"Index page status: {index_response.status_code}")

            # Test file upload and analysis
            test_file_path = os.path.join(os.path.dirname(__file__), 'uploads', 'test_sample.py')

            if os.path.exists(test_file_path):
                with open(test_file_path, 'rb') as f:
                    # Simulate file upload
                    upload_response = client.post('/', data={
                        'file': (f, 'test_sample.py')
                    }, content_type='multipart/form-data', follow_redirects=True)

                    print(f"Upload response status: {upload_response.status_code}")
                    print("Upload response data (first 500 chars):")
                    print(upload_response.data.decode()[:500])
            else:
                print(f"Test file not found: {test_file_path}")
        else:
            print("Login failed")

if __name__ == "__main__":
    test_ai_test_runner()