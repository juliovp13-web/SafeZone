import requests
import json
from datetime import datetime

def test_pix_subscription():
    """Test PIX subscription creation with a new user"""
    base_url = "https://global-user-admin.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Create unique email for this test
    test_email = f"pix_test_{datetime.now().strftime('%H%M%S')}@exemplo.com"
    
    print("🔍 Testing PIX Subscription Creation...")
    
    # 1. Register new user
    user_data = {
        "name": "Pedro PIX",
        "email": test_email,
        "password": "senha123",
        "street": "Rua do PIX",
        "number": "789",
        "neighborhood": "Centro",
        "resident_names": ["Pedro PIX"]
    }
    
    response = requests.post(f"{api_url}/register", json=user_data)
    if response.status_code != 200:
        print(f"❌ User registration failed: {response.text}")
        return False
    
    user_response = response.json()
    token = user_response['access_token']
    print(f"✅ User registered successfully")
    
    # 2. Create PIX subscription
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    subscription_data = {
        "payment_method": "pix"
    }
    
    response = requests.post(f"{api_url}/create-subscription", json=subscription_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ PIX subscription failed: {response.text}")
        return False
    
    pix_response = response.json()
    print(f"✅ PIX subscription created successfully")
    print(f"   Response: {json.dumps(pix_response, indent=2)}")
    
    # Verify PIX response fields
    if not pix_response.get('success'):
        print("❌ Success field is not True")
        return False
    
    if not pix_response.get('pix_code'):
        print("❌ PIX code is missing")
        return False
    
    print(f"✅ PIX code generated: {pix_response['pix_code']}")
    return True

def test_subscription_business_rules():
    """Test subscription business rules validation"""
    base_url = "https://global-user-admin.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("\n🔍 Testing Subscription Business Rules...")
    
    # Create unique email for this test
    test_email = f"business_test_{datetime.now().strftime('%H%M%S')}@exemplo.com"
    
    # 1. Register new user
    user_data = {
        "name": "Ana Business",
        "email": test_email,
        "password": "senha123",
        "street": "Rua Business",
        "number": "999",
        "neighborhood": "Centro",
        "resident_names": ["Ana Business"]
    }
    
    response = requests.post(f"{api_url}/register", json=user_data)
    if response.status_code != 200:
        print(f"❌ User registration failed: {response.text}")
        return False
    
    user_response = response.json()
    token = user_response['access_token']
    print(f"✅ User registered successfully")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 2. Create first subscription (should succeed)
    subscription_data = {
        "payment_method": "credit-card",
        "card_number": "1234567890123456",
        "card_name": "Ana Business",
        "card_expiry": "12/26",
        "card_cvv": "456"
    }
    
    response = requests.post(f"{api_url}/create-subscription", json=subscription_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ First subscription failed: {response.text}")
        return False
    
    print(f"✅ First subscription created successfully")
    
    # 3. Try to create second subscription (should fail)
    subscription_data2 = {
        "payment_method": "pix"
    }
    
    response = requests.post(f"{api_url}/create-subscription", json=subscription_data2, headers=headers)
    
    if response.status_code != 400:
        print(f"❌ Second subscription should have failed with 400, got {response.status_code}")
        return False
    
    error_response = response.json()
    if "já possui assinatura ativa" not in error_response.get('detail', ''):
        print(f"❌ Wrong error message: {error_response}")
        return False
    
    print(f"✅ Duplicate subscription correctly prevented")
    return True

def main():
    print("🚀 Running Additional Payment Tests")
    print("=" * 50)
    
    success_count = 0
    total_tests = 2
    
    if test_pix_subscription():
        success_count += 1
    
    if test_subscription_business_rules():
        success_count += 1
    
    print("\n" + "=" * 50)
    print("📊 ADDITIONAL TEST RESULTS")
    print("=" * 50)
    print(f"Tests Run: {total_tests}")
    print(f"Tests Passed: {success_count}")
    print(f"Tests Failed: {total_tests - success_count}")
    print(f"Success Rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("🎉 All additional tests passed!")
        return 0
    else:
        print("⚠️  Some additional tests failed!")
        return 1

if __name__ == "__main__":
    main()