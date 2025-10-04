#!/usr/bin/env python3
"""
SMS Gateway Setup and Configuration Script for Healthcare Message Queue
Automates installation, configuration validation, and database initialization
for SMS gateway integration with healthcare message queuing system.
"""
import os
import sys
import subprocess
import psycopg2
from pathlib import Path


def check_python_version():
    """Validates Python version compatibility for SMS gateway components.
    
    Ensures Python 3.8 or higher is available for asyncio and modern
    cryptography library support required by healthcare data encryption.
    
    Returns:
        bool: True if Python version meets minimum requirements.
    """
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True


def install_requirements():
    """Installs required Python packages from requirements file.
    
    Processes requirements_sms.txt to install all dependencies needed
    for SMS gateway operation including Flask, cryptography, and PostgreSQL drivers.
    
    Returns:
        bool: True if all packages installed successfully.
    """
    print("\n📦 Installing Python dependencies...")
    
    requirements_file = Path(__file__).parent / "requirements_sms.txt"
    
    if not requirements_file.exists():
        print("❌ requirements_sms.txt not found")
        return False
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def check_database_connection():
    """Validates database connectivity and message queue schema presence.
    
    Tests PostgreSQL connection using configured credentials and verifies
    that required message queue tables exist for SMS integration.
    
    Returns:
        bool: True if database connection and schema validation succeed.
    """
    print("\n🗄️  Checking database connection...")
    
    try:
        # Import config
        from sms_config import DATABASE
        
        # Test connection
        conn = psycopg2.connect(**DATABASE)
        with conn.cursor() as cur:
            # Check if mq schema exists
            cur.execute("""
                SELECT 1 FROM information_schema.schemata 
                WHERE schema_name = 'mq'
            """)
            
            if cur.fetchone():
                print("✅ Database connection successful")
                print("✅ Message queue schema found")
                
                # Check for required tables
                required_tables = [
                    'exchange', 'queue', 'message', 'message_waiting',
                    'health_data_rules', 'network_status'
                ]
                
                for table in required_tables:
                    cur.execute("""
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'mq' AND table_name = %s
                    """, (table,))
                    
                    if cur.fetchone():
                        print(f"✅ Table mq.{table} exists")
                    else:
                        print(f"⚠️  Table mq.{table} missing")
                
                return True
            else:
                print("❌ Message queue schema not found")
                print("Please run the database initialization scripts first")
                return False
                
    except ImportError:
        print("❌ Cannot import sms_config.py")
        print("Please configure sms_config.py first")
        return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def setup_sms_queues():
    """Creates SMS-specific message queues and healthcare data rules.
    
    Establishes health exchange, SMS routing queues with priority patterns,
    and default healthcare data classification rules for automated processing.
    
    Returns:
        bool: True if all SMS queues and rules created successfully.
    """
    print("\n📨 Setting up SMS message queues...")
    
    try:
        from sms_config import DATABASE
        
        conn = psycopg2.connect(**DATABASE)
        conn.autocommit = True
        
        with conn.cursor() as cur:
            # Create Health Exchange if not exists
            cur.execute("""
                INSERT INTO mq.exchange(exchange_name) 
                VALUES ('Health Exchange') 
                ON CONFLICT (exchange_name) DO NOTHING
            """)
            print("✅ Health Exchange created/verified")
            
            # Create SMS-specific queues
            sms_queues = [
                ('SMS Queue', r'^sms\..*$'),
                ('Critical SMS Queue', r'^sms\..*\.priority_1$'),
                ('High Priority SMS Queue', r'^sms\..*\.priority_2$'),
                ('Normal SMS Queue', r'^sms\..*\.priority_[3-5]$'),
                ('Outbound SMS Queue', r'^sms\.outbound\..*$'),
                ('Failed SMS Queue', r'^sms\.failed\..*$')
            ]
            
            for queue_name, pattern in sms_queues:
                cur.execute("""
                    INSERT INTO mq.queue(exchange_id, queue_name, routing_key_pattern)
                    SELECT e.exchange_id, %s, %s
                    FROM mq.exchange e 
                    WHERE e.exchange_name = 'Health Exchange'
                    ON CONFLICT (queue_name) DO NOTHING
                """, (queue_name, pattern))
                print(f"✅ Queue '{queue_name}' created/verified")
            
            # Verify health data rules exist
            cur.execute("SELECT COUNT(*) FROM mq.health_data_rules")
            rule_count = cur.fetchone()[0]
            
            if rule_count == 0:
                print("⚠️  No health data rules found")
                print("Creating default health data rules...")
                
                default_rules = [
                    ('hiv', 1, '1 hour'),
                    ('prescription', 2, '4 hours'),
                    ('lab_results', 3, '24 hours'),
                    ('appointment', 4, '72 hours'),
                    ('insurance', 5, '168 hours')
                ]
                
                for data_type, priority, ttl in default_rules:
                    cur.execute("""
                        INSERT INTO mq.health_data_rules(
                            data_type, priority_default, ttl, protocol_constraints
                        ) VALUES (%s, %s, %s::interval, %s)
                        ON CONFLICT (data_type) DO NOTHING
                    """, (data_type, priority, ttl, '{"sms", "http", "ussd"}'))
                    print(f"✅ Rule for '{data_type}' created")
            else:
                print(f"✅ Health data rules found: {rule_count} rules")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to setup SMS queues: {e}")
        return False


def create_startup_scripts():
    """Create startup scripts for SMS components"""
    print("\n📜 Creating startup scripts...")
    
    # Windows batch script
    windows_script = """@echo off
echo Starting SMS Gateway Services...

echo Starting SMS Webhook Server...
start "SMS Webhook" python sms_webhook_server.py

echo Starting SMS Gateway Adapter...
start "SMS Adapter" python -c "import asyncio; from sms_gateway_adapter import main; asyncio.run(main())"

echo SMS Gateway services started!
echo Check the console windows for status updates.
pause
"""
    
    # Unix shell script
    unix_script = """#!/bin/bash
echo "Starting SMS Gateway Services..."

echo "Starting SMS Webhook Server..."
python3 sms_webhook_server.py &
WEBHOOK_PID=$!

echo "Starting SMS Gateway Adapter..."
python3 -c "import asyncio; from sms_gateway_adapter import main; asyncio.run(main())" &
ADAPTER_PID=$!

echo "SMS Gateway services started!"
echo "Webhook Server PID: $WEBHOOK_PID"
echo "SMS Adapter PID: $ADAPTER_PID"

# Wait for both processes
wait $WEBHOOK_PID $ADAPTER_PID
"""
    
    try:
        # Write Windows script
        with open("start_sms_gateway.bat", "w") as f:
            f.write(windows_script)
        print("✅ Windows startup script created: start_sms_gateway.bat")
        
        # Write Unix script
        with open("start_sms_gateway.sh", "w") as f:
            f.write(unix_script)
        
        # Make Unix script executable
        os.chmod("start_sms_gateway.sh", 0o755)
        print("✅ Unix startup script created: start_sms_gateway.sh")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create startup scripts: {e}")
        return False


def test_webhook_server():
    """Test if webhook server can start"""
    print("\n🧪 Testing webhook server startup...")
    
    try:
        # Try to import the webhook server
        import sms_webhook_server
        print("✅ Webhook server module imports successfully")
        
        # Check if SMS adapter can be imported
        from sms_gateway_adapter import SMSGatewayAdapter
        print("✅ SMS Gateway Adapter imports successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing webhook server: {e}")
        return False


def show_configuration_guide():
    """Show configuration guidance"""
    print("\n" + "="*60)
    print("📋 CONFIGURATION GUIDE")
    print("="*60)
    
    print("\n1. SMS Gateway Configuration:")
    print("   - Edit sms_config.py")
    print("   - Set your SMS gateway API credentials")
    print("   - Configure facility phone number mappings")
    print("   - Set encryption password")
    
    print("\n2. Database Configuration:")
    print("   - Update DATABASE settings in sms_config.py")
    print("   - Ensure PostgreSQL is running")
    print("   - Verify message queue schema is initialized")
    
    print("\n3. Security Configuration:")
    print("   - Set strong encryption passwords")
    print("   - Configure HTTPS for production webhooks")
    print("   - Set up IP whitelisting for SMS gateway")
    
    print("\n4. Testing:")
    print("   - Run: python test_sms_integration.py")
    print("   - Test with sample SMS messages")
    print("   - Verify message queuing and processing")
    
    print("\n5. Production Deployment:")
    print("   - Use process manager (systemd, supervisor)")
    print("   - Set up reverse proxy (nginx)")
    print("   - Configure monitoring and logging")
    print("   - Set up SSL certificates")


def main():
    """Main setup function"""
    print("🏥 Healthcare SMS Gateway Setup")
    print("="*50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Check database
    if not check_database_connection():
        return False
    
    # Setup SMS queues
    if not setup_sms_queues():
        return False
    
    # Create startup scripts
    if not create_startup_scripts():
        return False
    
    # Test webhook server
    if not test_webhook_server():
        return False
    
    print("\n" + "="*50)
    print("🎉 SMS Gateway Setup Complete!")
    print("="*50)
    
    print("\n✅ Setup Summary:")
    print("   - Dependencies installed")
    print("   - Database connection verified")
    print("   - SMS queues configured")
    print("   - Startup scripts created")
    print("   - Components tested")
    
    # Show configuration guide
    show_configuration_guide()
    
    print("\n🚀 Next Steps:")
    print("1. Configure sms_config.py with your SMS gateway details")
    print("2. Start services: python sms_webhook_server.py")
    print("3. Run tests: python test_sms_integration.py")
    print("4. Send test SMS messages to your webhook endpoint")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n❌ Setup failed. Please fix the issues and try again.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")
        sys.exit(1)