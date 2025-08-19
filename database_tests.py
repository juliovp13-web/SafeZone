import requests
import json
from datetime import datetime
from pymongo import MongoClient
import os

def test_mongodb_connection():
    """Test MongoDB connection and data persistence"""
    print("🔍 Testing MongoDB Connection and Data Persistence...")
    
    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017")
        db = client["test_database"]
        
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Check collections
        collections = db.list_collection_names()
        print(f"✅ Available collections: {collections}")
        
        # Check users collection
        users_count = db.users.count_documents({})
        print(f"✅ Users in database: {users_count}")
        
        # Check subscriptions collection
        subscriptions_count = db.subscriptions.count_documents({})
        print(f"✅ Subscriptions in database: {subscriptions_count}")
        
        # Check alerts collection
        alerts_count = db.alerts.count_documents({})
        print(f"✅ Alerts in database: {alerts_count}")
        
        # Sample a user document to verify structure
        if users_count > 0:
            sample_user = db.users.find_one()
            required_fields = ['id', 'name', 'email', 'street', 'number', 'neighborhood', 'resident_names', 'created_at']
            
            for field in required_fields:
                if field not in sample_user:
                    print(f"❌ Missing field in user document: {field}")
                    return False
            
            print("✅ User document structure is correct")
        
        # Sample a subscription document to verify structure
        if subscriptions_count > 0:
            sample_subscription = db.subscriptions.find_one()
            required_fields = ['id', 'user_id', 'payment_method', 'status', 'start_date', 'next_payment', 'is_trial', 'amount', 'billing_cycle']
            
            for field in required_fields:
                if field not in sample_subscription:
                    print(f"❌ Missing field in subscription document: {field}")
                    return False
            
            print("✅ Subscription document structure is correct")
            
            # Verify business rules in data
            if sample_subscription['amount'] != 30.0:
                print(f"❌ Incorrect subscription amount: {sample_subscription['amount']}")
                return False
            
            if sample_subscription['is_trial'] != True:
                print(f"❌ Incorrect trial status: {sample_subscription['is_trial']}")
                return False
            
            print("✅ Subscription business rules are correctly applied")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        return False

def test_data_persistence_flow():
    """Test complete data persistence flow"""
    print("\n🔍 Testing Complete Data Persistence Flow...")
    
    base_url = "https://alertapp.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Create unique email for this test
    test_email = f"persistence_test_{datetime.now().strftime('%H%M%S')}@exemplo.com"
    
    # 1. Register user and verify in database
    user_data = {
        "name": "Carlos Persistence",
        "email": test_email,
        "password": "senha123",
        "street": "Rua Persistence",
        "number": "111",
        "neighborhood": "Centro",
        "resident_names": ["Carlos Persistence"]
    }
    
    response = requests.post(f"{api_url}/register", json=user_data)
    if response.status_code != 200:
        print(f"❌ User registration failed: {response.text}")
        return False
    
    user_response = response.json()
    token = user_response['access_token']
    user_id = user_response['user']['id']
    print(f"✅ User registered with ID: {user_id}")
    
    # Verify user in database
    try:
        client = MongoClient("mongodb://localhost:27017")
        db = client["test_database"]
        
        user_in_db = db.users.find_one({"id": user_id})
        if not user_in_db:
            print("❌ User not found in database")
            return False
        
        if user_in_db['email'] != test_email:
            print("❌ User email mismatch in database")
            return False
        
        print("✅ User correctly stored in database")
        
    except Exception as e:
        print(f"❌ Database verification failed: {str(e)}")
        return False
    
    # 2. Create subscription and verify in database
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    subscription_data = {
        "payment_method": "credit-card",
        "card_number": "1234567890123456",
        "card_name": "Carlos Persistence",
        "card_expiry": "12/27",
        "card_cvv": "789"
    }
    
    response = requests.post(f"{api_url}/create-subscription", json=subscription_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Subscription creation failed: {response.text}")
        return False
    
    print(f"✅ Subscription created successfully")
    
    # Verify subscription in database
    try:
        subscription_in_db = db.subscriptions.find_one({"user_id": user_id})
        if not subscription_in_db:
            print("❌ Subscription not found in database")
            return False
        
        if subscription_in_db['payment_method'] != 'credit-card':
            print("❌ Subscription payment method mismatch in database")
            return False
        
        if subscription_in_db['amount'] != 30.0:
            print("❌ Subscription amount mismatch in database")
            return False
        
        print("✅ Subscription correctly stored in database")
        
    except Exception as e:
        print(f"❌ Subscription database verification failed: {str(e)}")
        return False
    
    # 3. Create alert and verify in database
    alert_data = {"type": "invasão"}
    
    response = requests.post(f"{api_url}/alerts", json=alert_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Alert creation failed: {response.text}")
        return False
    
    alert_response = response.json()
    alert_id = alert_response['alert_id']
    print(f"✅ Alert created with ID: {alert_id}")
    
    # Verify alert in database
    try:
        alert_in_db = db.alerts.find_one({"id": alert_id})
        if not alert_in_db:
            print("❌ Alert not found in database")
            return False
        
        if alert_in_db['user_id'] != user_id:
            print("❌ Alert user_id mismatch in database")
            return False
        
        if alert_in_db['type'] != 'invasão':
            print("❌ Alert type mismatch in database")
            return False
        
        print("✅ Alert correctly stored in database")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Alert database verification failed: {str(e)}")
        return False

def main():
    print("🚀 Running Database Tests")
    print("=" * 50)
    
    success_count = 0
    total_tests = 2
    
    if test_mongodb_connection():
        success_count += 1
    
    if test_data_persistence_flow():
        success_count += 1
    
    print("\n" + "=" * 50)
    print("📊 DATABASE TEST RESULTS")
    print("=" * 50)
    print(f"Tests Run: {total_tests}")
    print(f"Tests Passed: {success_count}")
    print(f"Tests Failed: {total_tests - success_count}")
    print(f"Success Rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("🎉 All database tests passed!")
        return 0
    else:
        print("⚠️  Some database tests failed!")
        return 1

if __name__ == "__main__":
    main()