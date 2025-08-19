import requests
import sys
import json
from datetime import datetime

class SafeZoneFinalReviewTester:
    def __init__(self, base_url="https://alertapp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_issues = []
        self.minor_issues = []

    def log_test(self, name, success, details="", is_critical=True):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
            if is_critical:
                self.critical_issues.append(f"{name}: {details}")
            else:
                self.minor_issues.append(f"{name}: {details}")
        
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

    def test_priority_1_admin_login(self):
        """PRIORITY 1: Test admin login with specific credentials"""
        print("\n🎯 PRIORITY 1: LOGIN ADMIN - julio.csds@hotmail.com / Corinthians12@@@")
        print("=" * 70)
        
        login_data = {
            "email": "julio.csds@hotmail.com",
            "password": "Corinthians12@@@"
        }
        
        success, response = self.run_test(
            "Admin Login with Specific Credentials",
            "POST",
            "login",
            200,
            data=login_data
        )
        
        if not success:
            return False
        
        # Verify admin token and privileges
        self.token = response['access_token']
        user = response.get('user', {})
        
        if not user.get('is_admin') or not user.get('is_vip'):
            self.log_test("Admin Privileges Verification", False, f"Admin: {user.get('is_admin')}, VIP: {user.get('is_vip')}")
            return False
        
        print(f"✅ Admin login successful")
        print(f"✅ JWT Token: {self.token[:30]}...")
        print(f"✅ User is admin: {user.get('is_admin')}")
        print(f"✅ User is VIP: {user.get('is_vip')}")
        
        return True

    def test_priority_2_payment_system_trial(self):
        """PRIORITY 2: Test payment system with first month free"""
        print("\n🎯 PRIORITY 2: SISTEMA DE PAGAMENTO - PRIMEIRO MÊS GRÁTIS")
        print("=" * 70)
        
        # Create normal user to test trial system
        normal_user_data = {
            "name": "Usuario Trial",
            "email": f"trial_{datetime.now().strftime('%H%M%S')}@exemplo.com",
            "password": "senha123",
            "state": "SP",
            "city": "São Paulo",
            "street": "Rua Trial",
            "number": "100",
            "neighborhood": "Centro Trial",
            "resident_names": ["Usuario Trial"]
        }
        
        success, response = self.run_test(
            "Register Normal User for Trial Test",
            "POST",
            "register",
            200,
            data=normal_user_data
        )
        
        if not success:
            return False
        
        trial_token = response['access_token']
        old_token = self.token
        self.token = trial_token
        
        # Create subscription with trial
        subscription_data = {
            "payment_method": "pix"
        }
        
        success, sub_response = self.run_test(
            "Create Trial Subscription",
            "POST",
            "create-subscription",
            200,
            data=subscription_data
        )
        
        if not success:
            self.token = old_token
            return False
        
        # Verify trial message
        if "30 dias gratuitos" not in sub_response.get('message', ''):
            self.log_test("Trial Message Check", False, f"Message: {sub_response.get('message')}")
            self.token = old_token
            return False
        
        # Check subscription status
        success, status_response = self.run_test(
            "Check Trial Subscription Status",
            "GET",
            "subscription-status",
            200
        )
        
        self.token = old_token
        
        if not success:
            return False
        
        # Verify trial status
        if status_response.get('status') != 'trial':
            self.log_test("Trial Status Check", False, f"Status: {status_response.get('status')}")
            return False
        
        if status_response.get('is_blocked') != False:
            self.log_test("Trial Not Blocked Check", False, f"Is blocked: {status_response.get('is_blocked')}")
            return False
        
        print(f"✅ Trial subscription created successfully")
        print(f"✅ 30-day free trial active")
        print(f"✅ User not blocked during trial")
        print(f"✅ Days remaining: {status_response.get('days_remaining')}")
        
        return True

    def test_priority_3_swift_system(self):
        """PRIORITY 3: Test SWIFT wire transfer system"""
        print("\n🎯 PRIORITY 3: SISTEMA SWIFT WIRE TRANSFER")
        print("=" * 70)
        
        # Create user for SWIFT test
        swift_user_data = {
            "name": "Usuario SWIFT",
            "email": f"swift_{datetime.now().strftime('%H%M%S')}@exemplo.com",
            "password": "senha123",
            "state": "SP",
            "city": "São Paulo",
            "street": "Rua SWIFT",
            "number": "100",
            "neighborhood": "Centro SWIFT",
            "resident_names": ["Usuario SWIFT"]
        }
        
        success, response = self.run_test(
            "Register User for SWIFT Test",
            "POST",
            "register",
            200,
            data=swift_user_data
        )
        
        if not success:
            return False
        
        swift_token = response['access_token']
        old_token = self.token
        self.token = swift_token
        
        # Create SWIFT subscription
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
        
        self.token = old_token
        
        if not success:
            return False
        
        # Verify all SWIFT fields
        required_swift_fields = {
            'swift_code': 'SAFEBR2SXXX',
            'bank_name': 'SafeZone International Bank',
            'beneficiary': 'SafeZone Security Services'
        }
        
        all_swift_fields_valid = True
        
        for field, expected_value in required_swift_fields.items():
            if field not in swift_response:
                self.log_test(f"SWIFT Field {field}", False, f"Missing field: {field}")
                all_swift_fields_valid = False
            elif swift_response[field] != expected_value:
                self.log_test(f"SWIFT Field {field}", False, f"Expected: {expected_value}, Got: {swift_response[field]}")
                all_swift_fields_valid = False
        
        # Check dynamic fields exist
        if not swift_response.get('account_number'):
            self.log_test("SWIFT Account Number", False, "Account number is empty")
            all_swift_fields_valid = False
        
        if not swift_response.get('reference'):
            self.log_test("SWIFT Reference", False, "Reference is empty")
            all_swift_fields_valid = False
        
        if all_swift_fields_valid:
            print(f"✅ SWIFT Code: {swift_response['swift_code']}")
            print(f"✅ Bank Name: {swift_response['bank_name']}")
            print(f"✅ Account Number: {swift_response['account_number']}")
            print(f"✅ Beneficiary: {swift_response['beneficiary']}")
            print(f"✅ Reference: {swift_response['reference']}")
            print(f"✅ SWIFT wire transfer system fully operational")
        
        return all_swift_fields_valid

    def test_priority_4_admin_endpoints(self):
        """PRIORITY 4: Test admin endpoints functionality"""
        print("\n🎯 PRIORITY 4: ENDPOINTS ADMIN")
        print("=" * 70)
        
        if not self.token:
            self.log_test("Admin Endpoints Test", False, "No admin token available")
            return False
        
        # Test admin stats
        success1, stats_response = self.run_test(
            "Admin Stats Endpoint",
            "GET",
            "admin/stats",
            200
        )
        
        # Test admin users
        success2, users_response = self.run_test(
            "Admin Users Endpoint",
            "GET",
            "admin/users",
            200
        )
        
        # Test admin help messages
        success3, help_response = self.run_test(
            "Admin Help Messages Endpoint",
            "GET",
            "admin/help-messages",
            200
        )
        
        all_admin_endpoints_working = success1 and success2 and success3
        
        if all_admin_endpoints_working:
            print(f"✅ Admin Stats: {stats_response.get('total_users', 0)} users, {stats_response.get('total_subscriptions', 0)} subscriptions")
            print(f"✅ Admin Users: {len(users_response) if isinstance(users_response, list) else 0} users listed")
            print(f"✅ Admin Help: {len(help_response) if isinstance(help_response, list) else 0} help messages")
            print(f"✅ All admin endpoints operational")
        
        return all_admin_endpoints_working

    def test_priority_5_multiple_payment_methods(self):
        """PRIORITY 5: Test all payment methods work"""
        print("\n🎯 PRIORITY 5: MÚLTIPLOS MÉTODOS DE PAGAMENTO")
        print("=" * 70)
        
        payment_methods = [
            ("PIX", "pix", "pix_code"),
            ("Cartão", "credit-card", "payment_url"),
            ("Boleto", "boleto", "boleto_url")
        ]
        
        all_methods_working = True
        
        for method_name, method_code, expected_field in payment_methods:
            print(f"\n📱 Testing {method_name} payment method")
            
            # Create user for each method
            user_data = {
                "name": f"Usuario {method_name}",
                "email": f"{method_code}_{datetime.now().strftime('%H%M%S')}@exemplo.com",
                "password": "senha123",
                "state": "SP",
                "city": "São Paulo",
                "street": f"Rua {method_name}",
                "number": "100",
                "neighborhood": f"Centro {method_name}",
                "resident_names": [f"Usuario {method_name}"]
            }
            
            success, response = self.run_test(
                f"Register User for {method_name}",
                "POST",
                "register",
                200,
                data=user_data
            )
            
            if not success:
                all_methods_working = False
                continue
            
            method_token = response['access_token']
            old_token = self.token
            self.token = method_token
            
            # Create subscription
            subscription_data = {"payment_method": method_code}
            if method_code == "credit-card":
                subscription_data.update({
                    "card_number": "1234567890123456",
                    "card_name": f"Usuario {method_name}",
                    "card_expiry": "12/25",
                    "card_cvv": "123"
                })
            
            success, method_response = self.run_test(
                f"Create {method_name} Subscription",
                "POST",
                "create-subscription",
                200,
                data=subscription_data
            )
            
            self.token = old_token
            
            if success and expected_field in method_response:
                print(f"✅ {method_name} working: {method_response[expected_field]}")
            else:
                print(f"❌ {method_name} failed")
                all_methods_working = False
        
        return all_methods_working

    def run_final_review_tests(self):
        """Run final comprehensive review tests"""
        print("🚀 EXECUTANDO TESTES FINAIS CONFORME REVIEW REQUEST")
        print("=" * 80)
        print("CONTEXTO: Testar melhorias implementadas no sistema SafeZone")
        print("PRIORIDADES:")
        print("1. Login Admin (julio.csds@hotmail.com / Corinthians12@@@)")
        print("2. Sistema de Pagamento com primeiro mês grátis")
        print("3. Sistema SWIFT wire transfer")
        print("4. Endpoints Admin")
        print("5. Validação de múltiplos métodos de pagamento")
        print("=" * 80)
        
        # Run priority tests
        test1 = self.test_priority_1_admin_login()
        test2 = self.test_priority_2_payment_system_trial()
        test3 = self.test_priority_3_swift_system()
        test4 = self.test_priority_4_admin_endpoints()
        test5 = self.test_priority_5_multiple_payment_methods()
        
        # Calculate results
        priority_tests_passed = sum([test1, test2, test3, test4, test5])
        total_priority_tests = 5
        
        # Print final results
        print("\n" + "=" * 80)
        print("📊 RESULTADO FINAL DOS TESTES REVIEW REQUEST")
        print("=" * 80)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Total Tests Passed: {self.tests_passed}")
        print(f"Total Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Overall Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print(f"Priority Tests Passed: {priority_tests_passed}/{total_priority_tests}")
        print(f"Priority Success Rate: {(priority_tests_passed/total_priority_tests)*100:.1f}%")
        
        # Report critical issues
        if self.critical_issues:
            print(f"\n❌ CRITICAL ISSUES FOUND ({len(self.critical_issues)}):")
            for issue in self.critical_issues:
                print(f"   • {issue}")
        
        # Report minor issues
        if self.minor_issues:
            print(f"\n⚠️  MINOR ISSUES FOUND ({len(self.minor_issues)}):")
            for issue in self.minor_issues:
                print(f"   • {issue}")
        
        # Final verdict
        if priority_tests_passed == total_priority_tests and len(self.critical_issues) == 0:
            print("\n🎉 TODOS OS TESTES PRIORITÁRIOS PASSARAM!")
            print("✅ Sistema SafeZone está 100% funcional conforme solicitado")
            print("✅ Login admin operacional com credenciais específicas")
            print("✅ Sistema de pagamento com primeiro mês grátis funcionando")
            print("✅ Sistema SWIFT wire transfer implementado corretamente")
            print("✅ Endpoints admin operacionais")
            print("✅ Múltiplos métodos de pagamento funcionando")
            print("🚀 Sistema pronto para uso em produção!")
            return 0
        elif len(self.critical_issues) == 0:
            print("\n✅ SISTEMA FUNCIONAL COM PEQUENOS AJUSTES NECESSÁRIOS")
            print("✅ Funcionalidades principais operacionais")
            print("⚠️  Alguns testes menores falharam mas não afetam funcionalidade crítica")
            return 0
        else:
            print("\n❌ PROBLEMAS CRÍTICOS ENCONTRADOS!")
            print("⚠️  Sistema precisa de correções antes do uso")
            return 1

def main():
    tester = SafeZoneFinalReviewTester()
    return tester.run_final_review_tests()

if __name__ == "__main__":
    sys.exit(main())