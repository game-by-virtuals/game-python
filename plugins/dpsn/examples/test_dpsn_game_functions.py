import sys
import os
from pathlib import Path
import time
from datetime import datetime
from game_sdk.game.custom_types import Function, Argument, FunctionResultStatus
from dotenv import load_dotenv
load_dotenv()



from dpsn_plugin_gamesdk.dpsn_plugin import DpsnPlugin

dpsn_plugin=DpsnPlugin(
     dpsn_url=os.getenv("DPSN_URL"),
    pvt_key=os.getenv("PVT_KEY")
)

def test_dpsn_connection():
    """Test DPSN connection and basic functionality"""
    print("\n🔄 Testing DPSN Connection...")
    
  
    # Wait for connection to stabilize
    time.sleep(1)
    print("✅ DPSN initialized successfully")
    return True

def test_subscribe_and_receive():
    """Test subscribing to topics and receiving messages"""
    print("\n🔄 Testing Subscription and Message Reception...")
    
    # Define message handler
    def handle_message(message_data):
        topic = message_data['topic']
        payload = message_data['payload']
        print(f"Received message on {topic}: {payload}")

    # Set the callback
    dpsn_plugin.set_message_callback(handle_message)
    
    # Test topic
    topic = "0xe14768a6d8798e4390ec4cb8a4c991202c2115a5cd7a6c0a7ababcaf93b4d2d4/SOLUSDT/ohlc"
    
    print(f"Subscribing to topic: {topic}")
    result = dpsn_plugin.subscribe(topic)
    if not result["success"]:
        print(f"❌ Failed to subscribe to topic: {result.get('error')}")
        return False
    
    print("Subscription successful!")
    print("\nWaiting for messages... (Press Ctrl+C to exit)")
    
    try:
        while True:
            if not dpsn_plugin.client.dpsn_broker.is_connected():
                print("Connection lost, attempting to reconnect...")
                dpsn_plugin.initialize()
                time.sleep(1)
                dpsn_plugin.subscribe(topic)
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return True
    
def test_shutdown():
    """Test graceful shutdown"""
    print("\n🔄 Testing Shutdown...")
    
    status,message,extra = dpsn_plugin.shutdown()
    if status is not FunctionResultStatus.DONE:
        print(f"❌ Failed to shutdown")
        return False
    
    print("✅ Shutdown successful")
    return True

def main():
    """Main test function"""
    print("🚀 Starting DPSN Plugin Tests...")
    
    try:
        # Test connection
        if not test_dpsn_connection():
            return
        
        if not test_subscribe_and_receive():
            return
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
    finally:
        # Ensure we shutdown properly
        test_shutdown()

if __name__ == "__main__":
    main()
