import xmlrpc.client
import time

# Connect to server using its LAN IP (same server as vehicle signals)
server = xmlrpc.client.ServerProxy("http://127.0.0.1:8000/", allow_none=True)

def register_time_and_sync():
    """Register this client's time and trigger Berkeley synchronization"""
    print("=" * 60)
    print("🚶‍♂️ PEDESTRIAN CROSSING SIGNAL CONTROLLER 🚶‍♀️")
    print("=" * 60)
    
    # Get pedestrian signal time input
    while True:
        pedestrian_time = input("🕒 Enter Pedestrian Signal time (HH:MM:SS): ")
        try:
            # Validate format
            hour, minute, second = map(int, pedestrian_time.split(':'))
            if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                break
            else:
                print("❌ Invalid time values. Please use valid HH:MM:SS format.")
        except:
            print("❌ Invalid time format. Please use HH:MM:SS")
    
    print("📍 Connecting to Signal Manipulator Server...")
    
    try:
        # Register this client's time
        success = server.register_client_time("Pedestrian Signal", pedestrian_time)
        if success:
            print("✅ Pedestrian Signal time registered successfully!")
        else:
            print("❌ Failed to register time")
            return False
        
        # Wait a moment for synchronization
        print("⏳ Waiting for Berkeley Algorithm synchronization...")
        time.sleep(2)
        
        # Check for synchronized time
        sync_time = server.get_synchronized_time()
        if sync_time:
            print(f"\n🎯 FINAL SYNCHRONIZED TIME: {sync_time}")
            print("✅ All traffic systems are now synchronized!")
        else:
            print("⏳ Synchronization pending - waiting for all clients...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during time synchronization: {e}")
        return False

def pedestrian_signal_monitor():
    print("🚶‍♂️ Monitoring pedestrian crossing signals...")
    
    try:
        # Fetch each pedestrian message with its delay
        while True:
            msg = server.get_next_pedestrian_message()
            if msg is None:
                break
            print(f"🚶‍♂️ PEDESTRIAN: {msg}")

    except Exception as e:
        print("❌ Error communicating with server:", e)

def display_status():
    """Display current synchronized time"""
    try:
        sync_time = server.get_synchronized_time()
        if sync_time:
            print(f"⏰ Current synchronized time: {sync_time}")
    except:
        pass

if __name__ == "__main__":
    # First, handle time synchronization
    if not register_time_and_sync():
        print("❌ Failed to initialize. Exiting...")
        exit(1)
    
    print("\n" + "=" * 60)
    print("📍 Connected to Signal Manipulator Server")
    print("🔄 Pedestrian signals work opposite to vehicle signals")
    print("   - When vehicles at Junction 12 stop → Pedestrians at Junction 12 can cross")
    print("   - When vehicles at Junction 34 stop → Pedestrians at Junction 34 can cross")
    print("=" * 60)
    
    while True:
        try:
            # Wait for signal changes from the main controller
            display_status()
            pedestrian_signal_monitor()
            print(f"\n⏳ Waiting for next signal change...\n")
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Pedestrian signal monitor stopped manually.")
            break
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("🔄 Retrying connection in 5 seconds...")
            time.sleep(5)