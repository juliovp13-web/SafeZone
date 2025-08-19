import requests
import sys
import json
from datetime import datetime

class SafeZoneReviewTester:
    def __init__(self, base_url="https://alertapp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0

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

    def test_admin_login_specific_credentials(self):
        """Test 1: Login Admin com credenciais específicas"""
        print("\n🎯 TESTE 1: LOGIN ADMIN COM CREDENCIAIS ESPECÍFICAS")
        print("=" * 60)
        print("Credenciais: julio.csds@hotmail.com / Corinthians12@@@")
        
        login_data = {
            "email": "julio.csds@hotmail.com",
            "password": "Corinthians12@@@"
        }
        
        success, response = self.run_test(
            "Login Admin com Credenciais Específicas",
            "POST",
            "login",
            200,
            data=login_data
        )
        
        if success:
            self.token = response['access_token']
            user = response.get('user', {})
            
            # Verify admin privileges
            if not user.get('is_admin') or not user.get('is_vip'):
                self.log_test("Admin Privileges Check", False, f"Admin: {user.get('is_admin')}, VIP: {user.get('is_vip')}")
                return False
            
            print(f"✅ Admin login successful with specific credentials")
            print(f"✅ User is admin: {user.get('is_admin')}")
            print(f"✅ User is VIP: {user.get('is_vip')}")
            return True
        
        return False

    def test_payment_system_trial(self):
        """Test 2: Sistema de Pagamento - Primeiro mês grátis"""
        print("\n🎯 TESTE 2: SISTEMA DE PAGAMENTO - PRIMEIRO MÊS GRÁTIS")
        print("=" * 60)
        
        if not self.token:
            print("❌ No token available for payment test")
            return False
        
        # Test creating subscription with trial
        subscription_data = {
            "payment_method": "pix"
        }
        
        success, response = self.run_test(
            "Criar Assinatura com Trial Gratuito",
            "POST",
            "create-subscription",
            200,
            data=subscription_data
        )
        
        if not success:
            return False
        
        # Verify trial message
        if "30 dias gratuitos" not in response.get('message', ''):
            self.log_test("Trial Message Check", False, f"Message: {response.get('message')}")
            return False
        
        print(f"✅ Trial subscription created successfully")
        print(f"✅ Message contains '30 dias gratuitos': {response.get('message')}")
        
        # Check subscription status
        success, status_response = self.run_test(
            "Verificar Status da Assinatura Trial",
            "GET",
            "subscription-status",
            200
        )
        
        if not success:
            return False
        
        # Verify trial status
        if status_response.get('status') != 'trial':
            self.log_test("Trial Status Check", False, f"Status: {status_response.get('status')}")
            return False
        
        if status_response.get('is_blocked') != False:
            self.log_test("Trial Not Blocked Check", False, f"Is blocked: {status_response.get('is_blocked')}")
            return False
        
        print(f"✅ Subscription status is 'trial': {status_response.get('status')}")
        print(f"✅ User is not blocked: {status_response.get('is_blocked')}")
        print(f"✅ Days remaining: {status_response.get('days_remaining')}")
        
        return True

    def test_swift_payment_method(self):
        """Test 3: Sistema SWIFT Wire Transfer"""
        print("\n🎯 TESTE 3: SISTEMA SWIFT WIRE TRANSFER")
        print("=" * 60)
        
        # Create new user for SWIFT test
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
            "Registrar Usuário para Teste SWIFT",
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
            "Criar Assinatura SWIFT Wire Transfer",
            "POST",
            "create-subscription",
            200,
            data=swift_subscription_data
        )
        
        self.token = old_token
        
        if not success:
            return False
        
        # Verify SWIFT fields
        required_swift_fields = {
            'swift_code': 'SAFEBR2SXXX',
            'bank_name': 'SafeZone International Bank',
            'beneficiary': 'SafeZone Security Services'
        }
        
        for field, expected_value in required_swift_fields.items():
            if field not in swift_response:
                self.log_test(f"SWIFT Field {field}", False, f"Missing field: {field}")
                return False
            if swift_response[field] != expected_value:
                self.log_test(f"SWIFT Field {field}", False, f"Expected: {expected_value}, Got: {swift_response[field]}")
                return False
        
        # Check dynamic fields exist
        if not swift_response.get('account_number'):
            self.log_test("SWIFT Account Number", False, "Account number is empty")
            return False
        
        if not swift_response.get('reference'):
            self.log_test("SWIFT Reference", False, "Reference is empty")
            return False
        
        print(f"✅ SWIFT Code: {swift_response['swift_code']}")
        print(f"✅ Bank Name: {swift_response['bank_name']}")
        print(f"✅ Account Number: {swift_response['account_number']}")
        print(f"✅ Beneficiary: {swift_response['beneficiary']}")
        print(f"✅ Reference: {swift_response['reference']}")
        
        return True

    def test_multiple_payment_methods(self):
        """Test 4: Múltiplos Métodos de Pagamento"""
        print("\n🎯 TESTE 4: MÚLTIPLOS MÉTODOS DE PAGAMENTO")
        print("=" * 60)
        
        payment_methods = [
            ("PIX", "pix", "pix_code"),
            ("Cartão", "credit-card", "payment_url"),
            ("Boleto", "boleto", "boleto_url")
        ]
        
        all_methods_working = True
        
        for method_name, method_code, expected_field in payment_methods:
            print(f"\n📱 Testando método: {method_name}")
            
            # Create new user for each payment method
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
                f"Registrar Usuário {method_name}",
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
            
            # Create subscription with this method
            subscription_data = {"payment_method": method_code}
            if method_code == "credit-card":
                subscription_data.update({
                    "card_number": "1234567890123456",
                    "card_name": f"Usuario {method_name}",
                    "card_expiry": "12/25",
                    "card_cvv": "123"
                })
            
            success, method_response = self.run_test(
                f"Criar Assinatura {method_name}",
                "POST",
                "create-subscription",
                200,
                data=subscription_data
            )
            
            self.token = old_token
            
            if success and expected_field in method_response:
                print(f"✅ {method_name}: {method_response[expected_field]}")
            else:
                print(f"❌ {method_name} failed")
                all_methods_working = False
        
        return all_methods_working

    def test_admin_endpoints(self):
        """Test 5: Endpoints Admin"""
        print("\n🎯 TESTE 5: ENDPOINTS ADMIN")
        print("=" * 60)
        
        if not self.token:
            print("❌ No admin token available")
            return False
        
        admin_endpoints = [
            ("Admin Stats", "admin/stats"),
            ("Admin Users", "admin/users"),
            ("Admin Help Messages", "admin/help-messages")
        ]
        
        all_endpoints_working = True
        
        for endpoint_name, endpoint_path in admin_endpoints:
            success, response = self.run_test(
                endpoint_name,
                "GET",
                endpoint_path,
                200
            )
            
            if not success:
                all_endpoints_working = False
            else:
                print(f"✅ {endpoint_name} working")
        
        return all_endpoints_working

    def test_countries_data_validation(self):
        """Test 6: Validação de Dados de Países"""
        print("\n🎯 TESTE 6: VALIDAÇÃO DE DADOS DE PAÍSES")
        print("=" * 60)
        
        # Check if countries.js file exists and has proper structure
        try:
            # This would normally check the frontend countries file
            # For now, we'll test if the backend handles country codes properly
            
            # Test registration with different country codes
            test_countries = ["BRA", "USA", "ESP", "DEU", "FRA"]
            
            for country_code in test_countries:
                user_data = {
                    "name": f"Usuario {country_code}",
                    "email": f"country_{country_code.lower()}_{datetime.now().strftime('%H%M%S')}@exemplo.com",
                    "password": "senha123",
                    "state": "SP",
                    "city": "São Paulo",
                    "street": "Rua Internacional",
                    "number": "100",
                    "neighborhood": "Centro Internacional",
                    "resident_names": [f"Usuario {country_code}"],
                    "country_code": country_code
                }
                
                success, response = self.run_test(
                    f"Registrar Usuário {country_code}",
                    "POST",
                    "register",
                    200,
                    data=user_data
                )
                
                if success:
                    user = response.get('user', {})
                    if user.get('country_code') != country_code:
                        self.log_test(f"Country Code {country_code}", False, f"Expected: {country_code}, Got: {user.get('country_code')}")
                        return False
                    print(f"✅ Country {country_code} handled correctly")
                else:
                    return False
            
            return True
            
        except Exception as e:
            self.log_test("Countries Data Validation", False, f"Exception: {str(e)}")
            return False

    def run_review_tests(self):
        """Run all tests requested in the review"""
        print("🚀 EXECUTANDO TESTES CONFORME REVIEW REQUEST")
        print("=" * 70)
        print("CONTEXTO: Testar melhorias implementadas no sistema SafeZone")
        print("FOCO: Login Admin, Sistema de Pagamento, SWIFT, Endpoints Admin")
        print("=" * 70)
        
        # Run all review tests
        test1 = self.test_admin_login_specific_credentials()
        test2 = self.test_payment_system_trial()
        test3 = self.test_swift_payment_method()
        test4 = self.test_multiple_payment_methods()
        test5 = self.test_admin_endpoints()
        test6 = self.test_countries_data_validation()
        
        # Print final results
        print("\n" + "=" * 70)
        print("📊 RESULTADO DOS TESTES REVIEW REQUEST")
        print("=" * 70)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        all_tests_passed = all([test1, test2, test3, test4, test5, test6])
        
        if all_tests_passed:
            print("\n🎉 TODOS OS TESTES REVIEW REQUEST PASSARAM!")
            print("✅ Login admin funcionando com credenciais específicas")
            print("✅ Sistema de pagamento com primeiro mês grátis operacional")
            print("✅ Sistema SWIFT wire transfer implementado corretamente")
            print("✅ Múltiplos métodos de pagamento funcionando")
            print("✅ Endpoints admin operacionais")
            print("✅ Validação de dados de países funcionando")
            return 0
        else:
            print("\n❌ ALGUNS TESTES FALHARAM!")
            print("⚠️  Verificar problemas reportados acima")
            return 1

def main():
    tester = SafeZoneReviewTester()
    return tester.run_review_tests()

if __name__ == "__main__":
    sys.exit(main())