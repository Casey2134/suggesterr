#!/usr/bin/env python3
"""
Authentication API Tests
Tests the login, authentication state, and settings API endpoints
"""

import json
import requests
import sys
from time import sleep

class AuthAPITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, passed, message, details=""):
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}: {message}")
        if details:
            print(f"    Details: {details}")
        
        self.test_results.append({
            'name': test_name,
            'passed': passed,
            'message': message,
            'details': details
        })
    
    def test_current_user_unauthenticated(self):
        """Test current_user endpoint when not authenticated"""
        try:
            response = self.session.get(f"{self.base_url}/api/auth/current_user/")
            data = response.json()
            
            passed = response.status_code == 200 and data.get('user') is None
            self.log_test(
                "Current User - Unauthenticated",
                passed,
                "Should return null user when not authenticated",
                f"Status: {response.status_code}, Response: {data}"
            )
            return passed
        except Exception as e:
            self.log_test("Current User - Unauthenticated", False, f"Request failed: {str(e)}")
            return False
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login/",
                json={"username": "nonexistent", "password": "wrongpass"},
                headers={"Content-Type": "application/json"}
            )
            
            passed = response.status_code == 401
            self.log_test(
                "Login - Invalid Credentials",
                passed,
                "Should return 401 for invalid credentials",
                f"Status: {response.status_code}"
            )
            return passed
        except Exception as e:
            self.log_test("Login - Invalid Credentials", False, f"Request failed: {str(e)}")
            return False
    
    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        try:
            # First create a test user
            self.create_test_user()
            
            response = self.session.post(
                f"{self.base_url}/api/auth/login/",
                json={"username": "testuser", "password": "testpass123"},
                headers={"Content-Type": "application/json"}
            )
            data = response.json()
            
            passed = (response.status_code == 200 and 
                     data.get('success') is True and 
                     data.get('user', {}).get('username') == 'testuser')
            
            self.log_test(
                "Login - Valid Credentials",
                passed,
                "Should return 200 with user data for valid credentials",
                f"Status: {response.status_code}, Response: {data}"
            )
            return passed
        except Exception as e:
            self.log_test("Login - Valid Credentials", False, f"Request failed: {str(e)}")
            return False
    
    def test_current_user_authenticated(self):
        """Test current_user endpoint when authenticated"""
        try:
            response = self.session.get(f"{self.base_url}/api/auth/current_user/")
            data = response.json()
            
            passed = (response.status_code == 200 and 
                     data.get('user') is not None and
                     data.get('user', {}).get('username') == 'testuser')
            
            self.log_test(
                "Current User - Authenticated",
                passed,
                "Should return user data when authenticated",
                f"Status: {response.status_code}, Response: {data}"
            )
            return passed
        except Exception as e:
            self.log_test("Current User - Authenticated", False, f"Request failed: {str(e)}")
            return False
    
    def test_settings_get(self):
        """Test settings GET endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/settings/")
            data = response.json()
            
            passed = response.status_code == 200 and isinstance(data, dict)
            self.log_test(
                "Settings - GET",
                passed,
                "Should return settings object",
                f"Status: {response.status_code}, Response: {data}"
            )
            return passed
        except Exception as e:
            self.log_test("Settings - GET", False, f"Request failed: {str(e)}")
            return False
    
    def test_settings_post(self):
        """Test settings POST endpoint"""
        try:
            test_data = {
                "server_type": "jellyfin",
                "server_url": "http://localhost:8096",
                "preferred_language": "en"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/settings/",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            passed = response.status_code in [200, 201]
            self.log_test(
                "Settings - POST",
                passed,
                "Should accept settings update/create",
                f"Status: {response.status_code}, Data sent: {test_data}"
            )
            return passed
        except Exception as e:
            self.log_test("Settings - POST", False, f"Request failed: {str(e)}")
            return False
    
    def test_logout(self):
        """Test logout endpoint"""
        try:
            response = self.session.post(f"{self.base_url}/api/auth/logout/")
            data = response.json()
            
            passed = response.status_code == 200 and data.get('success') is True
            self.log_test(
                "Logout",
                passed,
                "Should successfully logout",
                f"Status: {response.status_code}, Response: {data}"
            )
            return passed
        except Exception as e:
            self.log_test("Logout", False, f"Request failed: {str(e)}")
            return False
    
    def test_current_user_after_logout(self):
        """Test current_user endpoint after logout"""
        try:
            response = self.session.get(f"{self.base_url}/api/auth/current_user/")
            data = response.json()
            
            passed = response.status_code == 200 and data.get('user') is None
            self.log_test(
                "Current User - After Logout",
                passed,
                "Should return null user after logout",
                f"Status: {response.status_code}, Response: {data}"
            )
            return passed
        except Exception as e:
            self.log_test("Current User - After Logout", False, f"Request failed: {str(e)}")
            return False
    
    def create_test_user(self):
        """Helper method to create test user"""
        try:
            # Use Django management command to create user
            import subprocess
            subprocess.run([
                "python", "manage.py", "shell", "-c",
                "from django.contrib.auth.models import User; "
                "User.objects.filter(username='testuser').delete(); "
                "User.objects.create_user('testuser', 'test@example.com', 'testpass123'); "
                "print('Test user created')"
            ], cwd="/Users/caseycutshall/Dev Projects/suggesterr", capture_output=True)
        except Exception as e:
            print(f"Warning: Could not create test user: {e}")
    
    def run_all_tests(self):
        """Run the complete test suite"""
        print("🔧 Starting Authentication API Tests...\n")
        
        # Test sequence that follows the user flow
        tests = [
            self.test_current_user_unauthenticated,
            self.test_login_invalid_credentials,
            self.test_login_valid_credentials,
            self.test_current_user_authenticated,
            self.test_settings_get,
            self.test_settings_post,
            self.test_logout,
            self.test_current_user_after_logout,
        ]
        
        for test in tests:
            test()
            sleep(0.1)  # Small delay between tests
        
        # Summary
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        total_tests = len(self.test_results)
        
        print(f"\n📊 Test Results Summary:")
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! Authentication system is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
            failed_tests = [r for r in self.test_results if not r['passed']]
            print("\nFailed tests:")
            for test in failed_tests:
                print(f"  - {test['name']}: {test['message']}")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    print("Authentication API Test Suite")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/api/auth/current_user/", timeout=5)
        print("✅ Server is responding\n")
    except requests.exceptions.RequestException:
        print("❌ Server is not running on localhost:8000")
        print("Please start the Django server with: python manage.py runserver")
        sys.exit(1)
    
    tester = AuthAPITester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)