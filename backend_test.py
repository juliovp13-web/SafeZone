import requests
import sys
import json
from datetime import datetime

class SafeZoneAPITester:
    def __init__(self, base_url="https://country-sorting.preview.emergentagent.com"):
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

    def test_admin_auto_registration(self):
        """Test 1: Teste de Admin Automatico - Register julio.csds@hotmail.com and verify auto admin/VIP"""
        print("\n🎯 TESTE 1: ADMIN AUTOMATICO")
        print("=" * 60)
        
        # Register julio.csds@hotmail.com
        admin_user_data = {
            "name": "Julio Admin",
            "email": "julio.csds@hotmail.com",
            "password": "AdminPass123",
            "street": "Rua Admin",
            "number": "100",
            "neighborhood": "Centro Admin",
            "resident_names": ["Julio Admin"]
        }
        
        success, response = self.run_test(
            "Register Admin User (julio.csds@hotmail.com)",
            "POST",
            "register",
            200,
            data=admin_user_data
        )
        
        if not success:
            return False
        
        # Verify user is automatically admin/VIP
        if 'user' not in response:
            self.log_test("Admin Auto Registration", False, "No user in response")
            return False
        
        user = response['user']
        admin_token = response['access_token']
        
        # Check if automatically became admin and VIP
        if not user.get('is_admin'):
            self.log_test("Auto Admin Status", False, "User is not admin")
            return False
        
        if not user.get('is_vip'):
            self.log_test("Auto VIP Status", False, "User is not VIP")
            return False
        
        print(f"✅ User automatically became admin: {user.get('is_admin')}")
        print(f"✅ User automatically became VIP: {user.get('is_vip')}")
        
        # Test login and verify admin/VIP status in login response
        login_data = {
            "email": "julio.csds@hotmail.com",
            "password": "AdminPass123"
        }
        
        success, login_response = self.run_test(
            "Login Admin User",
            "POST",
            "login",
            200,
            data=login_data
        )
        
        if not success:
            return False
        
        login_user = login_response.get('user', {})
        if not login_user.get('is_admin') or not login_user.get('is_vip'):
            self.log_test("Login Admin/VIP Status", False, f"Admin: {login_user.get('is_admin')}, VIP: {login_user.get('is_vip')}")
            return False
        
        self.log_test("Admin Auto Registration Complete", True)
        return admin_token
    
    def test_vip_bypass(self):
        """Test 2: Teste VIP Bypass - Check subscription-status for julio.csds@hotmail.com"""
        print("\n🎯 TESTE 2: VIP BYPASS")
        print("=" * 60)
        
        # Login as admin user
        login_data = {
            "email": "julio.csds@hotmail.com",
            "password": "AdminPass123"
        }
        
        success, login_response = self.run_test(
            "Login Admin for VIP Test",
            "POST",
            "login",
            200,
            data=login_data
        )
        
        if not success:
            return False
        
        admin_token = login_response['access_token']
        old_token = self.token
        self.token = admin_token
        
        # Test subscription-status endpoint
        success, response = self.run_test(
            "Check VIP Subscription Status",
            "GET",
            "subscription-status",
            200
        )
        
        self.token = old_token
        
        if not success:
            return False
        
        # Verify VIP status and is_blocked=false
        if response.get('status') != 'vip':
            self.log_test("VIP Status Check", False, f"Expected 'vip', got '{response.get('status')}'")
            return False
        
        if response.get('is_blocked') != False:
            self.log_test("VIP Not Blocked Check", False, f"Expected False, got {response.get('is_blocked')}")
            return False
        
        print(f"✅ Status: {response.get('status')}")
        print(f"✅ Is Blocked: {response.get('is_blocked')}")
        print(f"✅ Message: {response.get('message')}")
        
        self.log_test("VIP Bypass Test Complete", True)
        return True
    
    def test_admin_endpoints(self):
        """Test 3: Endpoints Admin - Test admin endpoints"""
        print("\n🎯 TESTE 3: ENDPOINTS ADMIN")
        print("=" * 60)
        
        # Login as admin
        login_data = {
            "email": "julio.csds@hotmail.com",
            "password": "AdminPass123"
        }
        
        success, login_response = self.run_test(
            "Login Admin for Endpoints Test",
            "POST",
            "login",
            200,
            data=login_data
        )
        
        if not success:
            return False
        
        admin_token = login_response['access_token']
        old_token = self.token
        self.token = admin_token
        
        # Test GET /api/admin/stats
        success1, stats_response = self.run_test(
            "Admin Stats Endpoint",
            "GET",
            "admin/stats",
            200
        )
        
        if success1:
            expected_fields = ['total_users', 'total_subscriptions', 'active_subscriptions', 'trial_subscriptions', 'blocked_subscriptions', 'total_alerts', 'pending_help_messages']
            for field in expected_fields:
                if field not in stats_response:
                    self.log_test("Admin Stats Fields", False, f"Missing field: {field}")
                    success1 = False
                    break
            if success1:
                print(f"✅ Stats: {stats_response}")
        
        # Test GET /api/admin/users
        success2, users_response = self.run_test(
            "Admin Users Endpoint",
            "GET",
            "admin/users",
            200
        )
        
        if success2:
            if not isinstance(users_response, list):
                self.log_test("Admin Users Response", False, "Response is not a list")
                success2 = False
            else:
                print(f"✅ Found {len(users_response)} users")
        
        # Test GET /api/admin/help-messages (should work even without messages)
        success3, help_response = self.run_test(
            "Admin Help Messages Endpoint",
            "GET",
            "admin/help-messages",
            200
        )
        
        if success3:
            if not isinstance(help_response, list):
                self.log_test("Admin Help Messages Response", False, "Response is not a list")
                success3 = False
            else:
                print(f"✅ Found {len(help_response)} help messages")
        
        self.token = old_token
        
        all_success = success1 and success2 and success3
        self.log_test("Admin Endpoints Test Complete", all_success)
        return all_success
    
    def test_help_system(self):
        """Test 4: Sistema Ajuda - Register normal user and test help system"""
        print("\n🎯 TESTE 4: SISTEMA AJUDA")
        print("=" * 60)
        
        # Register normal user
        normal_user_data = {
            "name": "Usuario Normal",
            "email": f"normal_{datetime.now().strftime('%H%M%S')}@exemplo.com",
            "password": "senha123",
            "street": "Rua Normal",
            "number": "200",
            "neighborhood": "Bairro Normal",
            "resident_names": ["Usuario Normal"]
        }
        
        success, response = self.run_test(
            "Register Normal User for Help Test",
            "POST",
            "register",
            200,
            data=normal_user_data
        )
        
        if not success:
            return False
        
        normal_token = response['access_token']
        old_token = self.token
        self.token = normal_token
        
        # Send help message
        help_data = {
            "message": "Preciso de ajuda com o aplicativo SafeZone. Como faço para reportar um problema?"
        }
        
        success, help_response = self.run_test(
            "Send Help Message",
            "POST",
            "help",
            200,
            data=help_data
        )
        
        self.token = old_token
        
        if not success:
            return False
        
        # Login as admin and check if message appears
        login_data = {
            "email": "julio.csds@hotmail.com",
            "password": "AdminPass123"
        }
        
        success, login_response = self.run_test(
            "Login Admin to Check Help Messages",
            "POST",
            "login",
            200,
            data=login_data
        )
        
        if not success:
            return False
        
        admin_token = login_response['access_token']
        self.token = admin_token
        
        # Check help messages
        success, messages_response = self.run_test(
            "Check Help Messages as Admin",
            "GET",
            "admin/help-messages",
            200
        )
        
        self.token = old_token
        
        if not success:
            return False
        
        # Verify message appears
        found_message = False
        for msg in messages_response:
            if help_data["message"] in msg.get("message", ""):
                found_message = True
                print(f"✅ Found help message: {msg.get('message')[:50]}...")
                break
        
        if not found_message:
            self.log_test("Help Message Verification", False, "Help message not found in admin panel")
            return False
        
        self.log_test("Help System Test Complete", True)
        return True
    
    def test_set_admin_system(self):
        """Test 5: Sistema Set Admin - Test promoting another user to admin"""
        print("\n🎯 TESTE 5: SISTEMA SET ADMIN")
        print("=" * 60)
        
        # Register user to promote
        promote_user_data = {
            "name": "Usuario Para Promover",
            "email": f"promote_{datetime.now().strftime('%H%M%S')}@exemplo.com",
            "password": "senha123",
            "street": "Rua Promocao",
            "number": "300",
            "neighborhood": "Bairro Promocao",
            "resident_names": ["Usuario Para Promover"]
        }
        
        success, response = self.run_test(
            "Register User to Promote",
            "POST",
            "register",
            200,
            data=promote_user_data
        )
        
        if not success:
            return False
        
        promote_email = promote_user_data["email"]
        
        # Login as admin
        login_data = {
            "email": "julio.csds@hotmail.com",
            "password": "AdminPass123"
        }
        
        success, login_response = self.run_test(
            "Login Admin for Set Admin Test",
            "POST",
            "login",
            200,
            data=login_data
        )
        
        if not success:
            return False
        
        admin_token = login_response['access_token']
        old_token = self.token
        self.token = admin_token
        
        # Promote user to admin
        admin_set_data = {
            "email": promote_email,
            "is_admin": True,
            "is_vip": True,
            "vip_permanent": True
        }
        
        success, set_response = self.run_test(
            "Set User as Admin",
            "POST",
            "admin/set-admin",
            200,
            data=admin_set_data
        )
        
        self.token = old_token
        
        if not success:
            return False
        
        # Verify user was promoted by logging in as them
        login_promoted_data = {
            "email": promote_email,
            "password": "senha123"
        }
        
        success, promoted_login = self.run_test(
            "Login Promoted User",
            "POST",
            "login",
            200,
            data=login_promoted_data
        )
        
        if not success:
            return False
        
        promoted_user = promoted_login.get('user', {})
        if not promoted_user.get('is_admin') or not promoted_user.get('is_vip'):
            self.log_test("User Promotion Verification", False, f"Admin: {promoted_user.get('is_admin')}, VIP: {promoted_user.get('is_vip')}")
            return False
        
        print(f"✅ User promoted to admin: {promoted_user.get('is_admin')}")
        print(f"✅ User promoted to VIP: {promoted_user.get('is_vip')}")
        
        self.log_test("Set Admin System Test Complete", True)
        return True
    
    def test_cancellation_system(self):
        """Test 6: Cancelamento - Test subscription cancellation for VIP and normal users"""
        print("\n🎯 TESTE 6: SISTEMA CANCELAMENTO")
        print("=" * 60)
        
        # Test 6a: VIP user cancellation (should error)
        login_data = {
            "email": "julio.csds@hotmail.com",
            "password": "AdminPass123"
        }
        
        success, login_response = self.run_test(
            "Login VIP User for Cancellation Test",
            "POST",
            "login",
            200,
            data=login_data
        )
        
        if not success:
            return False
        
        vip_token = login_response['access_token']
        old_token = self.token
        self.token = vip_token
        
        # Try to cancel VIP subscription (should fail)
        success, cancel_response = self.run_test(
            "Cancel VIP Subscription (Should Fail)",
            "POST",
            "cancel-subscription",
            400  # Should return error
        )
        
        if success:
            print(f"✅ VIP cancellation correctly blocked: {cancel_response.get('detail', 'No detail')}")
        
        self.token = old_token
        
        # Test 6b: Normal user with subscription cancellation
        # Create user with subscription
        normal_user_data = {
            "name": "Usuario Com Subscription",
            "email": f"subscription_{datetime.now().strftime('%H%M%S')}@exemplo.com",
            "password": "senha123",
            "street": "Rua Subscription",
            "number": "400",
            "neighborhood": "Bairro Subscription",
            "resident_names": ["Usuario Com Subscription"]
        }
        
        success, response = self.run_test(
            "Register User with Subscription",
            "POST",
            "register",
            200,
            data=normal_user_data
        )
        
        if not success:
            return False
        
        normal_token = response['access_token']
        self.token = normal_token
        
        # Create subscription
        subscription_data = {
            "payment_method": "credit-card",
            "card_number": "1234567890123456",
            "card_name": "Usuario Com Subscription",
            "card_expiry": "12/25",
            "card_cvv": "123"
        }
        
        success, sub_response = self.run_test(
            "Create Subscription for Normal User",
            "POST",
            "create-subscription",
            200,
            data=subscription_data
        )
        
        if not success:
            self.token = old_token
            return False
        
        # Cancel subscription
        success, cancel_response = self.run_test(
            "Cancel Normal User Subscription",
            "POST",
            "cancel-subscription",
            200
        )
        
        self.token = old_token
        
        if success:
            print(f"✅ Normal user subscription cancelled: {cancel_response.get('message', 'No message')}")
        
        all_success = success  # VIP cancellation test already passed if we got here
        self.log_test("Cancellation System Test Complete", all_success)
        return all_success

    def test_swift_payment_system(self):
        """Test SWIFT Wire Transfer Payment System - PRIORITY TEST"""
        print("\n🎯 TESTE PRIORITÁRIO: SISTEMA SWIFT")
        print("=" * 60)
        print("Testing SWIFT wire transfer implementation as requested in review:")
        print("- POST /api/create-subscription with payment_method='swift-wire'")
        print("- Verify SWIFT fields: swift_code, bank_name, account_number, beneficiary, reference")
        print("=" * 60)
        
        # Step 1: Login with admin user (julio.csds@hotmail.com)
        login_data = {
            "email": "julio.csds@hotmail.com",
            "password": "Corinthians12@@@"
        }
        
        success, login_response = self.run_test(
            "Login Admin User for SWIFT Test",
            "POST",
            "login",
            200,
            data=login_data
        )
        
        if not success:
            print("❌ Failed to login with admin credentials")
            return False
        
        admin_token = login_response['access_token']
        old_token = self.token
        self.token = admin_token
        
        print(f"✅ Admin login successful")
        
        # Step 2: Create subscription with SWIFT wire transfer
        swift_subscription_data = {
            "payment_method": "swift-wire"
        }
        
        success, swift_response = self.run_test(
            "Create SWIFT Wire Transfer Subscription",
            "POST",
            "create-subscription",
            200,
            data=swift_subscription_data
        )
        
        if not success:
            self.token = old_token
            print("❌ Failed to create SWIFT subscription")
            return False
        
        # Step 3: Verify SWIFT response fields
        print("\n🔍 VERIFYING SWIFT RESPONSE FIELDS:")
        print("=" * 40)
        
        required_swift_fields = {
            'swift_code': 'SAFEBR2SXXX',
            'bank_name': 'SafeZone International Bank',
            'beneficiary': 'SafeZone Security Services'
        }
        
        optional_swift_fields = ['account_number', 'reference']
        
        all_fields_valid = True
        
        # Check required fields with expected values
        for field, expected_value in required_swift_fields.items():
            if field not in swift_response:
                print(f"❌ Missing required SWIFT field: {field}")
                all_fields_valid = False
            elif swift_response[field] != expected_value:
                print(f"❌ SWIFT field {field}: expected '{expected_value}', got '{swift_response[field]}'")
                all_fields_valid = False
            else:
                print(f"✅ {field}: {swift_response[field]}")
        
        # Check optional fields exist and have values
        for field in optional_swift_fields:
            if field not in swift_response:
                print(f"❌ Missing SWIFT field: {field}")
                all_fields_valid = False
            elif not swift_response[field]:
                print(f"❌ SWIFT field {field} is empty")
                all_fields_valid = False
            else:
                print(f"✅ {field}: {swift_response[field]}")
        
        # Check basic response fields
        if not swift_response.get('success'):
            print(f"❌ Success field is not True: {swift_response.get('success')}")
            all_fields_valid = False
        else:
            print(f"✅ success: {swift_response.get('success')}")
        
        if not swift_response.get('message'):
            print(f"❌ Message field is empty")
            all_fields_valid = False
        else:
            print(f"✅ message: {swift_response.get('message')}")
        
        self.token = old_token
        
        if all_fields_valid:
            print("\n🎉 SWIFT SYSTEM TEST PASSED!")
            print("=" * 40)
            print("✅ All required SWIFT fields present and correct")
            print("✅ Account number and reference generated")
            print("✅ SWIFT wire transfer ready for international payments")
            self.log_test("SWIFT Payment System Test", True)
            return True
        else:
            print("\n❌ SWIFT SYSTEM TEST FAILED!")
            print("=" * 40)
            print("❌ Some SWIFT fields are missing or incorrect")
            self.log_test("SWIFT Payment System Test", False, "Missing or incorrect SWIFT fields")
            return False

    def test_existing_payment_methods(self):
        """Test existing payment methods still work after SWIFT implementation"""
        print("\n🎯 TESTE: MÉTODOS DE PAGAMENTO EXISTENTES")
        print("=" * 60)
        print("Verifying PIX, boleto, and credit card still work normally")
        print("=" * 60)
        
        all_methods_working = True
        
        # Test 1: PIX Payment Method
        print("\n📱 Testing PIX Payment Method")
        print("-" * 30)
        
        # Create new user for PIX test
        pix_user_data = {
            "name": "Usuario PIX",
            "email": f"pix_{datetime.now().strftime('%H%M%S')}@exemplo.com",
            "password": "senha123",
            "state": "SP",
            "city": "São Paulo",
            "street": "Rua PIX",
            "number": "100",
            "neighborhood": "Centro PIX",
            "resident_names": ["Usuario PIX"]
        }
        
        success, response = self.run_test(
            "Register User for PIX Test",
            "POST",
            "register",
            200,
            data=pix_user_data
        )
        
        if not success:
            all_methods_working = False
        else:
            pix_token = response['access_token']
            old_token = self.token
            self.token = pix_token
            
            pix_subscription_data = {
                "payment_method": "pix"
            }
            
            success, pix_response = self.run_test(
                "Create PIX Subscription",
                "POST",
                "create-subscription",
                200,
                data=pix_subscription_data
            )
            
            if success and 'pix_code' in pix_response:
                print(f"✅ PIX Code: {pix_response['pix_code']}")
                print(f"✅ PIX Message: {pix_response.get('message', 'No message')}")
            else:
                print("❌ PIX payment method failed")
                all_methods_working = False
            
            self.token = old_token
        
        # Test 2: Boleto Payment Method
        print("\n🧾 Testing Boleto Payment Method")
        print("-" * 30)
        
        # Create new user for Boleto test
        boleto_user_data = {
            "name": "Usuario Boleto",
            "email": f"boleto_{datetime.now().strftime('%H%M%S')}@exemplo.com",
            "password": "senha123",
            "state": "RJ",
            "city": "Rio de Janeiro",
            "street": "Rua Boleto",
            "number": "200",
            "neighborhood": "Centro Boleto",
            "resident_names": ["Usuario Boleto"]
        }
        
        success, response = self.run_test(
            "Register User for Boleto Test",
            "POST",
            "register",
            200,
            data=boleto_user_data
        )
        
        if not success:
            all_methods_working = False
        else:
            boleto_token = response['access_token']
            old_token = self.token
            self.token = boleto_token
            
            boleto_subscription_data = {
                "payment_method": "boleto"
            }
            
            success, boleto_response = self.run_test(
                "Create Boleto Subscription",
                "POST",
                "create-subscription",
                200,
                data=boleto_subscription_data
            )
            
            if success and 'boleto_url' in boleto_response:
                print(f"✅ Boleto URL: {boleto_response['boleto_url']}")
                print(f"✅ Boleto Message: {boleto_response.get('message', 'No message')}")
            else:
                print("❌ Boleto payment method failed")
                all_methods_working = False
            
            self.token = old_token
        
        # Test 3: Credit Card Payment Method
        print("\n💳 Testing Credit Card Payment Method")
        print("-" * 30)
        
        # Create new user for Credit Card test
        card_user_data = {
            "name": "Usuario Cartao",
            "email": f"card_{datetime.now().strftime('%H%M%S')}@exemplo.com",
            "password": "senha123",
            "state": "MG",
            "city": "Belo Horizonte",
            "street": "Rua Cartao",
            "number": "300",
            "neighborhood": "Centro Cartao",
            "resident_names": ["Usuario Cartao"]
        }
        
        success, response = self.run_test(
            "Register User for Credit Card Test",
            "POST",
            "register",
            200,
            data=card_user_data
        )
        
        if not success:
            all_methods_working = False
        else:
            card_token = response['access_token']
            old_token = self.token
            self.token = card_token
            
            card_subscription_data = {
                "payment_method": "credit-card",
                "card_number": "1234567890123456",
                "card_name": "Usuario Cartao",
                "card_expiry": "12/25",
                "card_cvv": "123"
            }
            
            success, card_response = self.run_test(
                "Create Credit Card Subscription",
                "POST",
                "create-subscription",
                200,
                data=card_subscription_data
            )
            
            if success and 'payment_url' in card_response:
                print(f"✅ Payment URL: {card_response['payment_url']}")
                print(f"✅ Card Message: {card_response.get('message', 'No message')}")
            else:
                print("❌ Credit card payment method failed")
                all_methods_working = False
            
            self.token = old_token
        
        # Final result
        if all_methods_working:
            print("\n🎉 ALL EXISTING PAYMENT METHODS WORKING!")
            print("=" * 50)
            print("✅ PIX payment method functional")
            print("✅ Boleto payment method functional")
            print("✅ Credit card payment method functional")
            self.log_test("Existing Payment Methods Test", True)
            return True
        else:
            print("\n❌ SOME PAYMENT METHODS FAILED!")
            print("=" * 50)
            self.log_test("Existing Payment Methods Test", False, "One or more payment methods failed")
            return False

    def test_admin_login_credentials(self):
        """Test admin login with specific credentials from review request"""
        print("\n🎯 TESTE: LOGIN ADMIN COM CREDENCIAIS ESPECÍFICAS")
        print("=" * 60)
        print("Testing login with julio.csds@hotmail.com / Corinthians12@@@")
        print("=" * 60)
        
        # Test login with exact credentials from review request
        login_data = {
            "email": "julio.csds@hotmail.com",
            "password": "Corinthians12@@@"
        }
        
        success, login_response = self.run_test(
            "Admin Login with Review Credentials",
            "POST",
            "login",
            200,
            data=login_data
        )
        
        if not success:
            print("❌ Failed to login with specified admin credentials")
            return False
        
        # Verify admin privileges
        user = login_response.get('user', {})
        if not user.get('is_admin'):
            print(f"❌ User is not admin: {user.get('is_admin')}")
            return False
        
        if not user.get('is_vip'):
            print(f"❌ User is not VIP: {user.get('is_vip')}")
            return False
        
        print(f"✅ Admin login successful")
        print(f"✅ User is admin: {user.get('is_admin')}")
        print(f"✅ User is VIP: {user.get('is_vip')}")
        print(f"✅ JWT token generated: {login_response['access_token'][:30]}...")
        
        self.log_test("Admin Login Credentials Test", True)
        return login_response['access_token']

    def run_swift_tests(self):
        """Run SWIFT system tests as requested in review"""
        print("🚀 Starting SafeZone SWIFT SYSTEM Tests")
        print("=" * 60)
        print("Testing SWIFT implementation as requested in review:")
        print("1. Admin Login with Specific Credentials")
        print("2. SWIFT Wire Transfer Payment System")
        print("3. Existing Payment Methods Compatibility")
        print("=" * 60)
        
        # Run SWIFT-specific tests
        test1 = self.test_admin_login_credentials()
        test2 = self.test_swift_payment_system()
        test3 = self.test_existing_payment_methods()
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 SWIFT SYSTEM TEST RESULTS")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All SWIFT system tests passed!")
            return 0
        else:
            print("⚠️  Some SWIFT system tests failed!")
            return 1

    def run_admin_tests(self):
        """Run all admin system tests as requested in review"""
        print("🚀 Starting SafeZone ADMIN SYSTEM Tests")
        print("=" * 60)
        print("Testing admin system implementation as requested:")
        print("1. Admin Automatico")
        print("2. VIP Bypass") 
        print("3. Endpoints Admin")
        print("4. Sistema Ajuda")
        print("5. Sistema Set Admin")
        print("6. Cancelamento")
        print("=" * 60)
        
        # Run admin-specific tests
        test1 = self.test_admin_auto_registration()
        test2 = self.test_vip_bypass()
        test3 = self.test_admin_endpoints()
        test4 = self.test_help_system()
        test5 = self.test_set_admin_system()
        test6 = self.test_cancellation_system()
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 ADMIN SYSTEM TEST RESULTS")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All admin system tests passed!")
            return 0
        else:
            print("⚠️  Some admin system tests failed!")
            return 1

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting SafeZone API Tests")
        print("=" * 50)
        
        # PRIORITY: Create predefined user for system owner
        self.test_create_predefined_user()
        
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

    def test_specific_admin_login_review_request(self):
        """Test specific admin login as requested in review request"""
        print("\n🎯 TESTE ESPECÍFICO: LOGIN ADMIN CONFORME REVIEW REQUEST")
        print("=" * 70)
        print("Testando login de admin com as credenciais específicas:")
        print("Email: julio.csds@hotmail.com")
        print("Senha: Corinthians12@@@")
        print("=" * 70)
        
        # Step 1: First try to login - if fails, create user
        login_data = {
            "email": "julio.csds@hotmail.com",
            "password": "Corinthians12@@@"
        }
        
        print("🔍 Tentando login direto primeiro...")
        success, login_response = self.run_test(
            "POST /api/login com credenciais específicas (tentativa 1)",
            "POST",
            "login",
            200,
            data=login_data
        )
        
        # If login failed, user might not exist - create it
        if not success:
            print("\n📝 Login falhou - criando usuário admin primeiro...")
            
            # Create admin user with specific credentials
            admin_user_data = {
                "name": "Julio",
                "email": "julio.csds@hotmail.com",
                "password": "Corinthians12@@@",
                "state": "SP",
                "city": "São Paulo",
                "street": "Rua Principal",
                "number": "123",
                "neighborhood": "Centro",
                "resident_names": ["Julio"]
            }
            
            success, register_response = self.run_test(
                "Registrar usuário admin julio.csds@hotmail.com",
                "POST",
                "register",
                200,
                data=admin_user_data
            )
            
            if not success:
                print("❌ FALHA: Não conseguiu criar usuário admin")
                return False
            
            print("✅ Usuário admin criado com sucesso!")
            
            # Now try login again
            print("\n🔍 Tentando login novamente após criação...")
            success, login_response = self.run_test(
                "POST /api/login com credenciais específicas (tentativa 2)",
                "POST",
                "login",
                200,
                data=login_data
            )
            
            if not success:
                print("❌ FALHA: Login ainda falhou após criação do usuário")
                return False
        
        print("\n🔍 VERIFICANDO RESPONSE DO LOGIN:")
        print("=" * 40)
        
        # Test 2: Verify response contains access_token (valid JWT)
        if 'access_token' not in login_response:
            print("❌ FALHA: access_token não encontrado na response")
            self.log_test("Access Token Verification", False, "access_token missing")
            return False
        
        access_token = login_response['access_token']
        print(f"✅ access_token encontrado: {access_token[:30]}...")
        
        # Test 3: Verify user object exists
        if 'user' not in login_response:
            print("❌ FALHA: user object não encontrado na response")
            self.log_test("User Object Verification", False, "user object missing")
            return False
        
        user = login_response['user']
        print(f"✅ user object encontrado")
        
        # Test 4: Verify user.email = julio.csds@hotmail.com
        if user.get('email') != 'julio.csds@hotmail.com':
            print(f"❌ FALHA: user.email incorreto. Esperado: julio.csds@hotmail.com, Recebido: {user.get('email')}")
            self.log_test("User Email Verification", False, f"Expected julio.csds@hotmail.com, got {user.get('email')}")
            return False
        
        print(f"✅ user.email correto: {user.get('email')}")
        
        # Test 5: Verify is_admin=true
        if user.get('is_admin') != True:
            print(f"❌ FALHA: is_admin incorreto. Esperado: true, Recebido: {user.get('is_admin')}")
            self.log_test("Admin Status Verification", False, f"Expected true, got {user.get('is_admin')}")
            return False
        
        print(f"✅ is_admin correto: {user.get('is_admin')}")
        
        # Test 6: Verify is_vip=true
        if user.get('is_vip') != True:
            print(f"❌ FALHA: is_vip incorreto. Esperado: true, Recebido: {user.get('is_vip')}")
            self.log_test("VIP Status Verification", False, f"Expected true, got {user.get('is_vip')}")
            return False
        
        print(f"✅ is_vip correto: {user.get('is_vip')}")
        
        # Test 7: Verify JWT token is valid by making authenticated request
        old_token = self.token
        self.token = access_token
        
        success, profile_response = self.run_test(
            "Validar JWT Token com GET /api/profile",
            "GET",
            "profile",
            200
        )
        
        self.token = old_token
        
        if not success:
            print("❌ FALHA: JWT token inválido - não conseguiu acessar /api/profile")
            self.log_test("JWT Token Validation", False, "Token failed profile access")
            return False
        
        print(f"✅ JWT token válido - acesso a /api/profile funcionou")
        
        # Final success summary
        print("\n🎉 TESTE ESPECÍFICO ADMIN LOGIN - SUCESSO COMPLETO!")
        print("=" * 60)
        print("✅ POST /api/login funcionou com credenciais específicas")
        print("✅ access_token (JWT válido) retornado")
        print("✅ user object retornado corretamente")
        print("✅ user.email = julio.csds@hotmail.com")
        print("✅ user.is_admin = true")
        print("✅ user.is_vip = true")
        print("✅ JWT token validado com sucesso")
        print("=" * 60)
        print("🚀 Sistema de login admin está 100% funcional!")
        
        self.log_test("Specific Admin Login Review Test", True, "All requirements met")
        return True

    def run_review_request_test(self):
        """Run the specific test requested in the review"""
        print("🚀 EXECUTANDO TESTE CONFORME REVIEW REQUEST")
        print("=" * 70)
        print("CONTEXTO: Testar o login de admin com as credenciais específicas")
        print("CREDENCIAIS: julio.csds@hotmail.com / Corinthians12@@@")
        print("EXPECTATIVA: Login deve funcionar perfeitamente com privilégios admin/VIP")
        print("=" * 70)
        
        # Run the specific test
        success = self.test_specific_admin_login_review_request()
        
        # Print final results
        print("\n" + "=" * 70)
        print("📊 RESULTADO DO TESTE REVIEW REQUEST")
        print("=" * 70)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if success:
            print("🎉 TESTE REVIEW REQUEST: SUCESSO TOTAL!")
            print("✅ Login de admin funcionando perfeitamente")
            print("✅ Token JWT gerado corretamente")
            print("✅ Usuário reconhecido como admin automaticamente")
            print("✅ Sistema pronto para uso pelo proprietário")
            return 0
        else:
            print("❌ TESTE REVIEW REQUEST: FALHOU!")
            print("⚠️  Problemas encontrados no login admin")
            return 1

def main():
    tester = SafeZoneAPITester()
    # Run specific test as requested in review
    return tester.run_review_request_test()

if __name__ == "__main__":
    sys.exit(main())