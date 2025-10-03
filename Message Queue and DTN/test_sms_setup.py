#!/usr/bin/env python3
"""
Simple test to verify SMS gateway components are working
"""
import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing SMS Gateway Component Imports...")
    
    # Test basic imports
    try:
        import flask
        print("✅ Flask imported")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        import psycopg2
        print("✅ PostgreSQL driver imported")
    except ImportError as e:
        print(f"❌ PostgreSQL driver import failed: {e}")
        return False
    
    try:
        import cryptography
        print("✅ Cryptography imported")
    except ImportError as e:
        print(f"❌ Cryptography import failed: {e}")
        return False
    
    try:
        import aiohttp
        print("✅ aiohttp imported")
    except ImportError as e:
        print(f"❌ aiohttp import failed: {e}")
        return False
    
    # Test SMS gateway components
    try:
        import sms_config
        print("✅ SMS config imported")
    except ImportError as e:
        print(f"❌ SMS config import failed: {e}")
        return False
    
    try:
        from sms_gateway_adapter import SMSGatewayAdapter
        print("✅ SMS Gateway Adapter imported")
    except ImportError as e:
        print(f"❌ SMS Gateway Adapter import failed: {e}")
        return False
    
    return True

def test_database_config():
    """Test database configuration"""
    print("\n🗄️ Testing Database Configuration...")
    
    try:
        from sms_config import DATABASE
        print(f"✅ Database config loaded")
        print(f"   Host: {DATABASE['host']}")
        print(f"   Database: {DATABASE['database']}")
        print(f"   User: {DATABASE['user']}")
        return True
    except Exception as e:
        print(f"❌ Database config error: {e}")
        return False

def test_sms_config():
    """Test SMS gateway configuration"""
    print("\n📱 Testing SMS Gateway Configuration...")
    
    try:
        from sms_config import SMS_GATEWAY, FACILITY_MAPPING
        print("✅ SMS gateway config loaded")
        print(f"   Gateway type: {type(SMS_GATEWAY)}")
        print(f"   Facilities mapped: {len(FACILITY_MAPPING)}")
        
        # Check required fields
        required_fields = ['api_key', 'send_url', 'sender_id']
        for field in required_fields:
            if field in SMS_GATEWAY:
                print(f"   ✅ {field}: configured")
            else:
                print(f"   ⚠️  {field}: not configured")
        
        return True
    except Exception as e:
        print(f"❌ SMS config error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 SMS Gateway Integration Test")
    print("="*50)
    
    tests = [
        test_imports,
        test_database_config, 
        test_sms_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("="*50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! SMS gateway is ready.")
        print("\n🚀 Next steps:")
        print("1. Update sms_config.py with your actual SMS gateway credentials")
        print("2. Ensure database is running and schema is initialized")
        print("3. Start webhook server: python sms_webhook_server.py")
        print("4. Run demo: python demo_sms_integration.py")
    else:
        print("❌ Some tests failed. Please fix issues before proceeding.")
        print("\n🔧 Common fixes:")
        print("- Install missing packages: pip install -r requirements_sms.txt")
        print("- Check sms_config.py configuration")
        print("- Verify database connection settings")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)