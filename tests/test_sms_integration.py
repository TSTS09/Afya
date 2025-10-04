#!/usr/bin/env python3
"""
SMS Integration Test Suite for Healthcare Message Queue
Validates SMS packet collection, queuing, prioritization, and secure forwarding.
Tests healthcare-specific features including encryption and protocol selection.
"""
import requests
import json
import time
import psycopg2
from datetime import datetime


class SMSIntegrationTest:
    def __init__(self, webhook_url, db_config):
        self.webhook_url = webhook_url
        self.db_config = db_config
        self.connection = None
        
    def connect_to_db(self):
        """Establishes database connection for test operations.
        
        Configures PostgreSQL connection with autocommit enabled
        for immediate test data visibility and cleanup.
        """
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.connection.autocommit = True
            print("✅ Connected to database")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
    
    def setup_test_environment(self):
        """Configures test environment with required exchanges and queues.
        
        Creates health exchange and SMS-specific queues with priority-based
        routing patterns for comprehensive integration testing.
        """
        print("\n🔧 Setting up test environment...")
        
        with self.connection.cursor() as cur:
            # Create health exchange if not exists
            cur.execute("""
                INSERT INTO mq.exchange(exchange_name) 
                VALUES ('Health Exchange') 
                ON CONFLICT (exchange_name) DO NOTHING
            """)
            
            # Create SMS-specific queue
            cur.execute("""
                INSERT INTO mq.queue(exchange_id, queue_name, routing_key_pattern)
                SELECT e.exchange_id, 'SMS Queue', '^sms\..*$'
                FROM mq.exchange e 
                WHERE e.exchange_name = 'Health Exchange'
                ON CONFLICT (queue_name) DO NOTHING
            """)
            
            # Create priority-based queues
            priority_queues = [
                ('Critical SMS Queue', '^sms\..*\.priority_1$'),
                ('High Priority SMS Queue', '^sms\..*\.priority_2$'),
                ('Normal SMS Queue', '^sms\..*\.priority_[3-5]$')
            ]
            
            for queue_name, pattern in priority_queues:
                cur.execute("""
                    INSERT INTO mq.queue(exchange_id, queue_name, routing_key_pattern)
                    SELECT e.exchange_id, %s, %s
                    FROM mq.exchange e 
                    WHERE e.exchange_name = 'Health Exchange'
                    ON CONFLICT (queue_name) DO NOTHING
                """, (queue_name, pattern))
        
        print("✅ Test environment setup complete")
    
    def test_webhook_health(self):
        """Validates webhook server availability and health status.
        
        Verifies that SMS webhook server is running and responding
        to health check requests before executing integration tests.
        
        Returns:
            bool: True if webhook server is healthy and accessible.
        """
        print("\n🏥 Testing webhook server health...")
        
        try:
            response = requests.get(f"{self.webhook_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Webhook server is healthy")
                return True
            else:
                print(f"❌ Webhook server unhealthy: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot reach webhook server: {e}")
            return False
    
    def send_test_sms(self, sms_data):
        """Transmits test SMS data to webhook endpoint for processing.
        
        Posts SMS data to webhook server and validates response status
        to confirm successful message acceptance and queuing.
        
        Args:
            sms_data: SMS message data in webhook format.
            
        Returns:
            bool: True if SMS was successfully processed by webhook.
        """
        try:
            response = requests.post(
                f"{self.webhook_url}/sms/webhook",
                json=sms_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SMS processed: {result['status']}")
                return True
            else:
                print(f"❌ SMS processing failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending SMS: {e}")
            return False
    
    def verify_message_in_queue(self, expected_data_type, expected_priority):
        """Validates message presence in queue with correct classification.
        
        Queries message queue database to confirm message was properly
        classified, prioritized, and queued according to healthcare rules.
        
        Args:
            expected_data_type: Expected healthcare data type classification.
            expected_priority: Expected priority level assignment.
            
        Returns:
            bool: True if message found with correct classification.
        """
        print(f"🔍 Checking for {expected_data_type} message in queue...")
        
        with self.connection.cursor() as cur:
            cur.execute("""
                SELECT m.*, q.queue_name, m.headers
                FROM mq.message m
                JOIN mq.queue q ON q.queue_id = m.queue_id
                WHERE m.headers->'data_type' = %s 
                AND m.priority = %s
                ORDER BY m.publish_time DESC
                LIMIT 1
            """, (expected_data_type, expected_priority))
            
            result = cur.fetchone()
            if result:
                print(f"✅ Found message in queue: {result[7]}")  # queue_name
                print(f"   Priority: {result[5]}")  # priority
                print(f"   Headers: {dict(result[8])}")  # headers
                return True
            else:
                print(f"❌ No {expected_data_type} message found")
                return False
    
    def test_hiv_critical_sms(self):
        """Tests HIV result SMS processing with critical priority assignment.
        
        Validates that HIV-related SMS messages receive highest priority
        classification and appropriate TTL for urgent medical data.
        
        Returns:
            bool: True if HIV SMS processed with priority 1 classification.
        """
        print("\n🩸 Testing HIV Critical SMS...")
        
        sms_data = {
            "from": "+233201234567",
            "to": "+233501234568",
            "text": json.dumps({
                "patient_id": "P001",
                "facility_id": "FACILITY_001",
                "data_type": "hiv",
                "result": "HIV Status: POSITIVE, CD4: 450 cells/μL",
                "urgency": "CRITICAL"
            }),
            "id": f"sms_hiv_{int(time.time())}"
        }
        
        success = self.send_test_sms(sms_data)
        if success:
            time.sleep(2)  # Allow processing time
            return self.verify_message_in_queue("hiv", 1)
        return False
    
    def test_prescription_sms(self):
        """Tests prescription SMS processing with high priority assignment.
        
        Validates that prescription-related SMS messages receive high priority
        classification appropriate for medication orders and pharmacy coordination.
        
        Returns:
            bool: True if prescription SMS processed with priority 2 classification.
        """
        print("\n💊 Testing Prescription SMS...")
        
        sms_data = {
            "from": "+233301234569",
            "to": "+233201234567",
            "text": "PRESCRIPTION: Patient P002 - Amoxicillin 500mg, 3x daily, 7 days. Pharmacy: Central Pharmacy",
            "id": f"sms_rx_{int(time.time())}"
        }
        
        success = self.send_test_sms(sms_data)
        if success:
            time.sleep(2)
            return self.verify_message_in_queue("prescription", 2)
        return False
    
    def test_lab_results_sms(self):
        """Test lab results SMS (medium priority)"""
        print("\n🧪 Testing Lab Results SMS...")
        
        sms_data = {
            "from": "+233501234568",
            "to": "+233201234567", 
            "text": "LAB RESULTS: Patient P003 - Glucose: 95mg/dL, Cholesterol: 180mg/dL, Normal range",
            "id": f"sms_lab_{int(time.time())}"
        }
        
        success = self.send_test_sms(sms_data)
        if success:
            time.sleep(2)
            return self.verify_message_in_queue("lab_results", 3)
        return False
    
    def test_structured_vs_plaintext(self):
        """Test both structured JSON and plain text SMS"""
        print("\n📝 Testing Structured vs Plain Text SMS...")
        
        # Structured JSON SMS
        structured_sms = {
            "from": "+233201234567",
            "to": "+233501234568",
            "text": json.dumps({
                "patient_id": "P004",
                "facility_id": "FACILITY_002",
                "appointment": "2025-10-15 14:30",
                "doctor": "Dr. Smith"
            }),
            "id": f"sms_struct_{int(time.time())}"
        }
        
        # Plain text SMS
        plaintext_sms = {
            "from": "+233301234569",
            "to": "+233201234567",
            "text": "Patient ID: P005\nInsurance: NHIS\nClaim Number: CL2025001\nStatus: Approved",
            "id": f"sms_plain_{int(time.time())}"
        }
        
        success1 = self.send_test_sms(structured_sms)
        time.sleep(1)
        success2 = self.send_test_sms(plaintext_sms)
        
        return success1 and success2
    
    def test_message_encryption(self):
        """Test that sensitive messages are encrypted"""
        print("\n🔐 Testing Message Encryption...")
        
        # Send sensitive HIV data
        sensitive_sms = {
            "from": "+233201234567",
            "to": "+233501234568",
            "text": "Patient P006 HIV test result: POSITIVE. CD4 count: 320. Start ART immediately.",
            "id": f"sms_encrypt_{int(time.time())}"
        }
        
        success = self.send_test_sms(sensitive_sms)
        if success:
            time.sleep(2)
            
            # Check if message was encrypted
            with self.connection.cursor() as cur:
                cur.execute("""
                    SELECT body, headers
                    FROM mq.message m
                    WHERE m.headers->'encrypted' = 'true'
                    ORDER BY m.publish_time DESC
                    LIMIT 1
                """)
                
                result = cur.fetchone()
                if result:
                    print("✅ Message was encrypted")
                    body = json.loads(result[0])
                    print(f"   Encrypted content length: {len(body['content'])}")
                    return True
                else:
                    print("❌ No encrypted message found")
                    return False
        return False
    
    def check_queue_statistics(self):
        """Check overall queue statistics"""
        print("\n📊 Queue Statistics:")
        
        with self.connection.cursor() as cur:
            cur.execute("""
                SELECT 
                    q.queue_name,
                    COUNT(mw.message_id) as waiting_count,
                    COUNT(CASE WHEN m.priority = 1 THEN 1 END) as critical_count,
                    COUNT(CASE WHEN m.priority = 2 THEN 1 END) as high_count,
                    AVG(m.priority) as avg_priority
                FROM mq.queue q
                LEFT JOIN mq.message_waiting mw ON mw.queue_id = q.queue_id
                LEFT JOIN mq.message m ON m.message_id = mw.message_id
                WHERE q.queue_name LIKE '%SMS%'
                GROUP BY q.queue_name
                ORDER BY waiting_count DESC
            """)
            
            results = cur.fetchall()
            for row in results:
                queue_name, waiting, critical, high, avg_priority = row
                print(f"   {queue_name}:")
                print(f"     Waiting: {waiting or 0}")
                print(f"     Critical: {critical or 0}")
                print(f"     High Priority: {high or 0}")
                print(f"     Avg Priority: {avg_priority or 0:.1f}")
    
    def test_sms_status_endpoint(self):
        """Test the SMS status endpoint"""
        print("\n📈 Testing SMS Status Endpoint...")
        
        try:
            response = requests.get(f"{self.webhook_url}/sms/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                print("✅ SMS Status Retrieved:")
                print(f"   Status: {status['status']}")
                stats = status.get('statistics', {})
                print(f"   Waiting Messages: {stats.get('waiting_messages', 0)}")
                print(f"   Critical Messages: {stats.get('critical_messages', 0)}")
                return True
            else:
                print(f"❌ Status endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error getting status: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all SMS integration tests"""
        print("🚀 Starting Comprehensive SMS Integration Test")
        print("=" * 60)
        
        # Connect to database
        self.connect_to_db()
        
        # Setup test environment
        self.setup_test_environment()
        
        # Test results
        results = {}
        
        # Run tests
        results['webhook_health'] = self.test_webhook_health()
        results['hiv_critical'] = self.test_hiv_critical_sms()
        results['prescription'] = self.test_prescription_sms()
        results['lab_results'] = self.test_lab_results_sms()
        results['structured_vs_plain'] = self.test_structured_vs_plaintext()
        results['encryption'] = self.test_message_encryption()
        results['status_endpoint'] = self.test_sms_status_endpoint()
        
        # Show queue statistics
        self.check_queue_statistics()
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY:")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\n🏆 Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! SMS integration is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the logs for details.")
        
        return passed == total


def main():
    """Main function to run SMS integration tests"""
    
    # Configuration
    WEBHOOK_URL = "http://localhost:5000"
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'afya_prototype',
        'user': 'postgres',
        'password': 'your_password'
    }
    
    print("SMS Integration Test for Healthcare Message Queue")
    print("Make sure the webhook server is running on http://localhost:5000")
    print("Press Enter to continue, or Ctrl+C to cancel...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nTest cancelled.")
        return
    
    # Run tests
    test_runner = SMSIntegrationTest(WEBHOOK_URL, DB_CONFIG)
    success = test_runner.run_comprehensive_test()
    
    if success:
        print("\n🚀 Next Steps:")
        print("1. Configure your actual SMS gateway API credentials")
        print("2. Update facility phone number mappings")
        print("3. Set up SSL/TLS for production webhook endpoint")
        print("4. Configure monitoring and alerting")
        print("5. Test with real SMS gateway")
    else:
        print("\n🔧 Troubleshooting:")
        print("1. Check if webhook server is running: python sms_webhook_server.py")
        print("2. Verify database connection and schema")
        print("3. Check logs: sms_webhook.log and sms_gateway.log")
        print("4. Ensure all dependencies are installed")


if __name__ == "__main__":
    main()