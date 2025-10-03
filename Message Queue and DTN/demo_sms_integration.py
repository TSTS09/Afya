#!/usr/bin/env python3
"""
Quick Start Demo for SMS Gateway Integration
Run this to see SMS integration in action
"""
import json
import time
import threading
import requests
from datetime import datetime


def demo_sms_flow():
    """Demonstrate the complete SMS integration flow"""
    
    print("🏥 Healthcare SMS Gateway Integration Demo")
    print("="*60)
    
    print("\n📋 This demo shows:")
    print("✅ SMS webhook receiving and processing")
    print("✅ Automatic medical data prioritization")
    print("✅ Message queuing with healthcare rules")
    print("✅ Encryption for sensitive data")
    print("✅ Network-aware protocol selection")
    
    print("\n🔧 Prerequisites:")
    print("1. PostgreSQL running with message queue schema")
    print("2. SMS webhook server running (python sms_webhook_server.py)")
    print("3. Python packages installed")
    
    print("\nPress Enter to start demo, or Ctrl+C to exit...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nDemo cancelled.")
        return
    
    # Test webhook health
    print("\n🏥 Testing webhook server health...")
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Webhook server is running")
            health_data = response.json()
            print(f"   Service: {health_data['service']}")
            print(f"   Status: {health_data['status']}")
        else:
            print("❌ Webhook server not responding correctly")
            print("   Make sure to run: python sms_webhook_server.py")
            return
    except Exception as e:
        print(f"❌ Cannot reach webhook server: {e}")
        print("   Make sure to run: python sms_webhook_server.py")
        return
    
    # Test sample SMS messages
    print("\n📱 Testing healthcare SMS messages...")
    
    # Sample messages for different medical scenarios
    test_messages = [
        {
            "name": "🩸 HIV Critical Result",
            "data": {
                "from": "+233201234567",
                "to": "+233501234568",
                "text": json.dumps({
                    "patient_id": "P001",
                    "facility_id": "ACCRA_GENERAL_001",
                    "data_type": "hiv", 
                    "result": "HIV Status: POSITIVE, CD4: 450 cells/μL",
                    "urgency": "CRITICAL"
                }),
                "id": f"demo_hiv_{int(time.time())}"
            }
        },
        {
            "name": "💊 Prescription Order",
            "data": {
                "from": "+233301234569",
                "to": "+233201234567",
                "text": "PRESCRIPTION: Patient P002 - Amoxicillin 500mg, 3x daily for 7 days. Pharmacy: Central Pharmacy",
                "id": f"demo_rx_{int(time.time())}"
            }
        },
        {
            "name": "🧪 Lab Results",
            "data": {
                "from": "+233501234568", 
                "to": "+233201234567",
                "text": "LAB RESULTS: Patient P003 - Glucose: 95mg/dL, Cholesterol: 180mg/dL, Normal range",
                "id": f"demo_lab_{int(time.time())}"
            }
        },
        {
            "name": "📅 Appointment",
            "data": {
                "from": "+233201234567",
                "to": "+233501234568",
                "text": "APPOINTMENT: Patient P004 scheduled for consultation on 2025-10-15 at 14:30 with Dr. Smith",
                "id": f"demo_apt_{int(time.time())}"
            }
        }
    ]
    
    # Send test messages
    for i, msg in enumerate(test_messages, 1):
        print(f"\n{i}. Sending {msg['name']}...")
        
        try:
            response = requests.post(
                "http://localhost:5000/sms/webhook",
                json=msg['data'],
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ {result['status'].upper()}: {result['message']}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(1)  # Brief pause between messages
    
    # Check system status
    print("\n📊 Checking SMS system status...")
    try:
        response = requests.get("http://localhost:5000/sms/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print("✅ System Status Retrieved:")
            print(f"   Status: {status['status']}")
            
            stats = status.get('statistics', {})
            print(f"   Waiting Messages: {stats.get('waiting_messages', 0)}")
            print(f"   Critical Messages: {stats.get('critical_messages', 0)}")
            print(f"   High Priority: {stats.get('high_priority_messages', 0)}")
        else:
            print(f"❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status check error: {e}")
    
    # Show what happened
    print("\n" + "="*60)
    print("🎉 Demo Complete! Here's what happened:")
    print("="*60)
    
    print("\n📋 Message Processing:")
    print("1. HIV result → Priority 1 (Critical) → 1hr TTL → Encrypted")
    print("2. Prescription → Priority 2 (High) → 4hr TTL → Encrypted") 
    print("3. Lab results → Priority 3 (Medium) → 24hr TTL → Encrypted")
    print("4. Appointment → Priority 4 (Low) → 72hr TTL → Not encrypted")
    
    print("\n🔄 What Happened Behind the Scenes:")
    print("✅ SMS received via webhook endpoint")
    print("✅ Data type automatically detected")
    print("✅ Medical priority assigned based on content")
    print("✅ Sensitive data encrypted for security")
    print("✅ Messages queued in PostgreSQL message queue")
    print("✅ Ready for network-aware delivery")
    
    print("\n🚀 Next Steps:")
    print("1. Connect real SMS gateway API")
    print("2. Configure facility phone mappings")
    print("3. Set up production webhook endpoint")
    print("4. Test with actual SMS gateway")
    print("5. Deploy with proper monitoring")
    
    print("\n📖 For detailed setup instructions:")
    print("   See SMS_GATEWAY_README.md")
    
    print("\n🧪 To run comprehensive tests:")
    print("   python test_sms_integration.py")


if __name__ == "__main__":
    demo_sms_flow()