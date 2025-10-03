#!/usr/bin/env python3
"""
tests/run_all_tests.py
Complete test runner for the message queue and DTN system
"""
import sys
import os
import time
import traceback
import psycopg2
from datetime import datetime
from pathlib import Path

# Import test classes (assuming they're in the same directory structure)
sys.path.append('.')
try:
    from unit.test_basic_mq import BasicMQTest
    from health_scenarios.test_lab_results import HealthDataTest
    from integration.test_full_workflow import IntegrationTest
    
    # Try to import SMS integration test
    try:
        from test_sms_integration import SMSIntegrationTest
        SMS_TESTS_AVAILABLE = True
    except ImportError:
        print("⚠️  SMS Integration tests not available")
        print("   Make sure test_sms_integration.py is in the tests directory")
        print("   And SMS gateway components are installed")
        SMS_TESTS_AVAILABLE = False
        
except ImportError:
    print("Import Error: Make sure test files are in the correct directory structure")
    print("Expected structure:")
    print("tests/")
    print("├── unit/test_basic_mq.py")
    print("├── health_scenarios/test_lab_results.py")
    print("├── integration/test_full_workflow.py")
    print("├── test_sms_integration.py")
    print("└── run_all_tests.py")
    sys.exit(1)

class TestRunner:
    def __init__(self, db_config):
        self.db_config = db_config
        self.test_results = {}
        self.start_time = None
        self.sql_dir = Path(__file__).parent.parent / 'Message Queue and DTN' / 'src'
        
    def check_schema_exists(self):
        """Check if the mq schema exists"""
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM information_schema.schemata WHERE schema_name = 'mq'")
                exists = cur.fetchone() is not None
            conn.close()
            return exists
        except Exception:
            return False
    
    def initialize_schema(self):
        """Initialize the database schema from SQL files"""
        print("Initializing database schema...")
        
        # Define the correct order of SQL files
        sql_files = [
            '000_initialize.sql',
            '001_tables.sql',
            '001a_health_tables.sql',
            '002a_health_triggers.sql',  # Use enhanced version instead of 002_triggers.sql
            '003_exchange_procedures.sql',
            '004_consumer_procedures.sql',
            '005_producer_procedures.sql',
            '007_health_functions.sql',
            '008_monitoring_views.sql'
        ]
        
        try:
            conn = psycopg2.connect(**self.db_config)
            conn.autocommit = True
            
            with conn.cursor() as cur:
                # Drop existing schema if it exists
                cur.execute("DROP SCHEMA IF EXISTS mq CASCADE")
                print("✓ Dropped existing mq schema")
                
                # Execute each SQL file in order
                for sql_file in sql_files:
                    file_path = self.sql_dir / sql_file
                    if file_path.exists():
                        print(f"   Executing {sql_file}...")
                        with open(file_path, 'r', encoding='utf-8') as f:
                            sql_content = f.read()
                            # Execute as a single transaction instead of splitting
                            # This preserves PostgreSQL dollar-quoted strings
                            cur.execute(sql_content)
                        print(f"   ✓ {sql_file} executed successfully")
                    else:
                        print(f"   ⚠ Warning: {sql_file} not found")
                        
            conn.close()
            print("✓ Database schema initialized successfully")
            return True
            
        except Exception as e:
            print(f"✗ Schema initialization failed: {e}")
            print(f"SQL directory: {self.sql_dir}")
            traceback.print_exc()
            return False
    
    def setup_database(self):
        """Ensure database is properly set up before testing"""
        print("Setting up test database...")
        
        # Always reinitialize schema for clean tests
        print("Reinitializing schema for clean test environment...")
        if not self.initialize_schema():
            return False
        
        try:
            # Connect to database
            conn = psycopg2.connect(**self.db_config)
            conn.autocommit = True
            
            with conn.cursor() as cur:
                # Clean up any existing test data safely
                try:
                    cur.execute("""
                        DELETE FROM mq.message_intake 
                        WHERE exchange_id IN (
                            SELECT exchange_id FROM mq.exchange 
                            WHERE exchange_name LIKE '%Test%'
                        )
                    """)
                    
                    cur.execute("DELETE FROM mq.exchange WHERE exchange_name LIKE '%Test%'")
                    
                    # Close any existing channels
                    cur.execute("CALL mq.close_dead_channels()")
                    
                except psycopg2.Error as e:
                    print(f"Warning during cleanup: {e}")
                    # Continue anyway - this might be expected on first run
                
                print("✓ Database cleaned and ready for testing")
                
            conn.close()
            
        except Exception as e:
            print(f"✗ Database setup failed: {e}")
            return False
            
        return True
        
    def run_test_suite(self, test_class, test_name):
        """Run a specific test suite and capture results"""
        print(f"\n{'='*60}")
        print(f"Running {test_name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        success = False
        error_message = None
        
        try:
            tester = test_class(self.db_config)
            result = tester.run_all_tests()
            success = True
            
            # Store any metrics returned
            if isinstance(result, (int, float)):
                self.test_results[test_name]['metrics'] = result
                
        except Exception as e:
            error_message = str(e)
            print(f"✗ {test_name} failed: {error_message}")
            traceback.print_exc()
            
        duration = time.time() - start_time
        
        self.test_results[test_name] = {
            'success': success,
            'duration': duration,
            'error': error_message
        }
        
        if success:
            print(f"✓ {test_name} completed successfully in {duration:.2f}s")
        else:
            print(f"✗ {test_name} failed after {duration:.2f}s")
            
        return success
        
    def check_system_health(self):
        """Check overall system health before and after tests"""
        print("\nChecking system health...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                # Check for waiting messages
                cur.execute("""
                    SELECT q.queue_name, COUNT(mw.message_id) as waiting_count
                    FROM mq.queue q
                    LEFT JOIN mq.message_waiting mw ON mw.queue_id = q.queue_id
                    GROUP BY q.queue_name
                    HAVING COUNT(mw.message_id) > 0
                """)
                waiting_messages = cur.fetchall()
                
                # Check for active channels
                cur.execute("SELECT COUNT(*) FROM mq.channel")
                active_channels = cur.fetchone()[0]
                
                # Check for failed messages
                cur.execute("SELECT COUNT(*) FROM mq.failed_messages WHERE failed_at > now() - interval '1 hour'")
                recent_failures = cur.fetchone()[0]
                
            conn.close()
            
            print(f"Active channels: {active_channels}")
            print(f"Recent failures: {recent_failures}")
            
            if waiting_messages:
                print("Waiting messages by queue:")
                for queue_name, count in waiting_messages:
                    print(f"  {queue_name}: {count} messages")
            else:
                print("No waiting messages")
                
        except Exception as e:
            print(f"Health check failed: {e}")
            
    def generate_report(self):
        """Generate a comprehensive test report"""
        total_duration = time.time() - self.start_time
        
        print(f"\n{'='*60}")
        print(f"TEST REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Total Duration: {total_duration:.2f}s")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\nDetailed Results:")
        print(f"{'Test Suite':<30} {'Status':<10} {'Duration':<10} {'Notes'}")
        print("-" * 70)
        
        for test_name, result in self.test_results.items():
            status = "PASSED" if result['success'] else "FAILED"
            duration = f"{result['duration']:.2f}s"
            notes = ""
            
            if 'metrics' in result:
                notes = f"Throughput: {result['metrics']:.1f} msg/s"
            elif result['error']:
                notes = result['error'][:30] + "..." if len(result['error']) > 30 else result['error']
                
            print(f"{test_name:<30} {status:<10} {duration:<10} {notes}")
            
        # Overall assessment
        if failed_tests == 0:
            print(f"\n🎉 ALL TESTS PASSED! System is ready for production.")
        elif failed_tests <= 1:
            print(f"\n⚠️  Minor issues detected. Review failed tests before deployment.")
        else:
            print(f"\n❌ Multiple test failures. System needs attention before deployment.")
            
    def run_all_tests(self):
        """Run the complete test suite"""
        self.start_time = time.time()
        
        print("🚀 Starting Message Queue & DTN System Test Suite")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Setup
        if not self.setup_database():
            print("Database setup failed. Aborting tests.")
            return False
            
        # Initial health check
        self.check_system_health()
        
        # Run test suites
        test_suites = [
            (BasicMQTest, "Basic Message Queue Tests"),
            (HealthDataTest, "Health Data Priority Tests"),
            (IntegrationTest, "Integration & Performance Tests"),
        ]
        
        all_passed = True
        for test_class, test_name in test_suites:
            success = self.run_test_suite(test_class, test_name)
            all_passed = all_passed and success
            
        # Final health check
        print(f"\nFinal system health check:")
        self.check_system_health()
        
        # Generate report
        self.generate_report()
        
        return all_passed

def main():
    """Main function to run tests"""
    # Database configuration - CHANGE THESE VALUES
    db_config = {
        'host': 'localhost',
        'database': 'pg_mq_poc',
        'user': 'postgres',
        'password': 'Christelle09123',
        'port': 5433
    }
    
    # Validate database connection first
    try:
        test_conn = psycopg2.connect(**db_config)
        test_conn.close()
        print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("\nPlease check:")
        print("1. PostgreSQL is running")
        print("2. Database 'pg_mq_poc' exists")
        print("3. Username and password are correct")
        print("4. You've run the rebuild.sh script to set up the schema")
        return False
        
    # Run tests
    runner = TestRunner(db_config)
    success = runner.run_all_tests()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)