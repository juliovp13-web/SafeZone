import requests
import sys
import json
from datetime import datetime

class SafeZoneAPITester:
    def __init__(self, base_url="https://payment-flow-test.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user_email = f"teste_{datetime.now().strftime('%H%M%S')}@exemplo.com"

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        if details:
            print(f"   Details: {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        
        # Default headers
        default_headers = {'Content-Type': 'application/json'}
        if self.token:
            default_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            default_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers, timeout=10)

            print(f"   Response Status: {response.status_code}")
            
            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
                print(f"   Response Data: {json.dumps(response_data, indent=2)}")
            except:
                response_data = {}
                print(f"   Response Text: {response.text}")

            if success:
                self.log_test(name, True)
                return True, response_data
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}")
                return False, response_data

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root Endpoint", "GET", "", 200)

    def test_user_registration(self):
        """Test user registration"""
        user_data = {
            "name": "João Silva",
            "email": self.test_user_email,
            "password": "senha123",
            "street": "Rua das Flores",
            "number": "123",
            "neighborhood": "Centro",
            "resident_names": ["João Silva", "Maria Silva"]
        }
        
        success, response = self.run_test(
            "User Registration", 
            "POST", 
            "register", 
            200, 
            data=user_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            if 'user' in response:
                self.user_id = response['user']['id']
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

    def test_user_login(self):
        """Test user login with registered credentials"""
        login_data = {
            "email": self.test_user_email,
            "password": "senha123"
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "login",
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            if 'user' in response:
                self.user_id = response['user']['id']
            print(f"   Login successful, token: {self.token[:20]}...")
            return True
        return False

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        login_data = {
            "email": "invalid@email.com",
            "password": "wrongpassword"
        }
        
        success, response = self.run_test(
            "Invalid Login",
            "POST",
            "login",
            401,
            data=login_data
        )
        return success

    def test_get_profile(self):
        """Test getting user profile"""
        if not self.token:
            self.log_test("Get Profile", False, "No token available")
            return False
            
        success, response = self.run_test(
            "Get Profile",
            "GET",
            "profile",
            200
        )
        
        if success:
            expected_fields = ['id', 'name', 'email', 'street', 'number', 'neighborhood']
            for field in expected_fields:
                if field not in response:
                    self.log_test("Profile Fields Check", False, f"Missing field: {field}")
                    return False
            self.log_test("Profile Fields Check", True)
        
        return success

    def test_create_alert_invasion(self):
        """Test creating invasion alert"""
        if not self.token:
            self.log_test("Create Invasion Alert", False, "No token available")
            return False
            
        alert_data = {"type": "invasão"}
        
        success, response = self.run_test(
            "Create Invasion Alert",
            "POST",
            "alerts",
            200,
            data=alert_data
        )
        
        if success and 'alert_id' in response:
            print(f"   Alert ID: {response['alert_id']}")
            return True
        return False

    def test_create_alert_robbery(self):
        """Test creating robbery alert"""
        if not self.token:
            self.log_test("Create Robbery Alert", False, "No token available")
            return False
            
        alert_data = {"type": "roubo"}
        
        success, response = self.run_test(
            "Create Robbery Alert",
            "POST",
            "alerts",
            200,
            data=alert_data
        )
        
        return success

    def test_create_alert_emergency(self):
        """Test creating emergency alert"""
        if not self.token:
            self.log_test("Create Emergency Alert", False, "No token available")
            return False
            
        alert_data = {"type": "emergência"}
        
        success, response = self.run_test(
            "Create Emergency Alert",
            "POST",
            "alerts",
            200,
            data=alert_data
        )
        
        return success

    def test_get_alerts(self):
        """Test getting alerts for neighborhood"""
        if not self.token:
            self.log_test("Get Alerts", False, "No token available")
            return False
            
        success, response = self.run_test(
            "Get Alerts",
            "GET",
            "alerts",
            200
        )
        
        if success:
            if isinstance(response, list):
                print(f"   Found {len(response)} alerts")
                if len(response) > 0:
                    alert = response[0]
                    expected_fields = ['id', 'type', 'user_name', 'street', 'number', 'neighborhood', 'timestamp']
                    for field in expected_fields:
                        if field not in alert:
                            self.log_test("Alert Fields Check", False, f"Missing field: {field}")
                            return False
                    self.log_test("Alert Fields Check", True)
                return True
            else:
                self.log_test("Get Alerts", False, "Response is not a list")
                return False
        
        return success

    def test_create_subscription_credit_card(self):
        """Test creating subscription with credit card"""
        if not self.token:
            self.log_test("Create Credit Card Subscription", False, "No token available")
            return False
            
        subscription_data = {
            "payment_method": "credit-card",
            "card_number": "1234567890123456",
            "card_name": "João Silva",
            "card_expiry": "12/25",
            "card_cvv": "123"
        }
        
        success, response = self.run_test(
            "Create Credit Card Subscription",
            "POST",
            "create-subscription",
            200,
            data=subscription_data
        )
        
        if success:
            expected_fields = ['success', 'message']
            for field in expected_fields:
                if field not in response:
                    self.log_test("Subscription Response Check", False, f"Missing field: {field}")
                    return False
            
            if response.get('success') != True:
                self.log_test("Subscription Success Check", False, "Success field is not True")
                return False
                
            self.log_test("Subscription Response Check", True)
        
        return success

    def test_create_subscription_pix(self):
        """Test creating subscription with PIX"""
        if not self.token:
            self.log_test("Create PIX Subscription", False, "No token available")
            return False
            
        subscription_data = {
            "payment_method": "pix"
        }
        
        success, response = self.run_test(
            "Create PIX Subscription",
            "POST",
            "create-subscription",
            400,  # Should fail because user already has subscription
            data=subscription_data
        )
        
        return success

    def test_create_subscription_boleto(self):
        """Test creating subscription with boleto"""
        # Create a new user for this test
        new_email = f"boleto_{datetime.now().strftime('%H%M%S')}@exemplo.com"
        user_data = {
            "name": "Maria Boleto",
            "email": new_email,
            "password": "senha123",
            "street": "Rua do Boleto",
            "number": "456",
            "neighborhood": "Centro",
            "resident_names": ["Maria Boleto"]
        }
        
        # Register new user
        success, response = self.run_test(
            "Register User for Boleto Test",
            "POST",
            "register",
            200,
            data=user_data
        )
        
        if not success:
            return False
            
        # Save current token
        old_token = self.token
        self.token = response['access_token']
        
        subscription_data = {
            "payment_method": "boleto"
        }
        
        success, response = self.run_test(
            "Create Boleto Subscription",
            "POST",
            "create-subscription",
            200,
            data=subscription_data
        )
        
        # Restore original token
        self.token = old_token
        
        if success and 'boleto_url' in response:
            print(f"   Boleto URL: {response['boleto_url']}")
            return True
        
        return success

    def test_create_predefined_user(self):
        """Test creating the predefined user for system owner"""
        print("\n🎯 CREATING PREDEFINED USER FOR SYSTEM OWNER")
        print("=" * 60)
        
        # Predefined user data as specified in the review request
        predefined_user_data = {
            "name": "Julio",
            "email": "julio.csds@hotmail.com",
            "password": "Corinthians12@@@",
            "street": "Rua Principal",
            "number": "123",
            "neighborhood": "Centro",
            "resident_names": ["Julio"]
        }
        
        print(f"📝 Creating user: {predefined_user_data['name']}")
        print(f"📧 Email: {predefined_user_data['email']}")
        print(f"🏠 Address: {predefined_user_data['street']}, {predefined_user_data['number']}, {predefined_user_data['neighborhood']}")
        print(f"👥 Residents: {predefined_user_data['resident_names']}")
        
        # Step 1: Register the predefined user
        success, response = self.run_test(
            "Register Predefined User (Julio)",
            "POST",
            "register",
            200,
            data=predefined_user_data
        )
        
        if not success:
            print("❌ Failed to create predefined user")
            return False
        
        # Verify registration response
        if 'user' not in response or 'access_token' not in response:
            self.log_test("Predefined User Registration Response", False, "Missing user or access_token in response")
            return False
        
        predefined_token = response['access_token']
        predefined_user = response['user']
        
        print(f"✅ User created successfully!")
        print(f"🆔 User ID: {predefined_user['id']}")
        print(f"🔑 JWT Token: {predefined_token[:30]}...")
        
        # Step 2: Test login with predefined credentials
        login_data = {
            "email": "julio.csds@hotmail.com",
            "password": "Corinthians12@@@"
        }
        
        success, login_response = self.run_test(
            "Login with Predefined Credentials",
            "POST",
            "login",
            200,
            data=login_data
        )
        
        if not success:
            print("❌ Failed to login with predefined credentials")
            return False
        
        # Verify login response
        if 'user' not in login_response or 'access_token' not in login_response:
            self.log_test("Predefined User Login Response", False, "Missing user or access_token in login response")
            return False
        
        login_token = login_response['access_token']
        login_user = login_response['user']
        
        print(f"✅ Login successful!")
        print(f"🔑 New JWT Token: {login_token[:30]}...")
        
        # Step 3: Verify JWT token works by getting profile
        # Save current token and use predefined user token
        old_token = self.token
        self.token = login_token
        
        success, profile_response = self.run_test(
            "Get Predefined User Profile",
            "GET",
            "profile",
            200
        )
        
        # Restore original token
        self.token = old_token
        
        if not success:
            print("❌ Failed to get profile with predefined user token")
            return False
        
        # Step 4: Verify user information matches
        expected_data = {
            "name": "Julio",
            "email": "julio.csds@hotmail.com",
            "street": "Rua Principal",
            "number": "123",
            "neighborhood": "Centro",
            "resident_names": ["Julio"]
        }
        
        for key, expected_value in expected_data.items():
            if profile_response.get(key) != expected_value:
                self.log_test("Predefined User Data Verification", False, f"Field {key}: expected {expected_value}, got {profile_response.get(key)}")
                return False
        
        print("✅ All user data verified correctly!")
        
        # Final summary
        print("\n🎉 PREDEFINED USER CREATION COMPLETE!")
        print("=" * 60)
        print(f"✅ User registered successfully")
        print(f"✅ Login working with correct credentials")
        print(f"✅ JWT token generated and validated")
        print(f"✅ User information returned correctly")
        print(f"📧 Email: julio.csds@hotmail.com")
        print(f"🔑 Password: Corinthians12@@@")
        print(f"🆔 User ID: {predefined_user['id']}")
        print("🚀 System owner can now use these credentials to test the application!")
        
        self.log_test("Complete Predefined User Setup", True, "All steps completed successfully")
        return True

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting SafeZone API Tests")
        print("=" * 50)
        
        # Basic API tests
        self.test_root_endpoint()
        
        # Authentication tests
        self.test_user_registration()
        self.test_invalid_login()
        
        # Profile tests (requires authentication)
        self.test_get_profile()
        
        # Alert tests (requires authentication)
        self.test_create_alert_invasion()
        self.test_create_alert_robbery()
        self.test_create_alert_emergency()
        self.test_get_alerts()
        
        # Subscription tests (requires authentication)
        self.test_create_subscription_credit_card()
        self.test_create_subscription_pix()  # Should fail - duplicate subscription
        self.test_create_subscription_boleto()  # New user
        
        # Print final results
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS")
        print("=" * 50)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed!")
            return 1

def main():
    tester = SafeZoneAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())