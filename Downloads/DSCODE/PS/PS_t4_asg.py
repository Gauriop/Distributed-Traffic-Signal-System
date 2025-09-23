import xmlrpc.client
import time

server = xmlrpc.client.ServerProxy("http://127.0.0.1:8000/", allow_none=True)

def register_time_and_sync():
    """Register this client's time and trigger Berkeley synchronization"""
    print("=" * 60)
    print("🚶‍♂️ PEDESTRIAN CROSSING SIGNAL CONTROLLER 🚶‍♀️")
    print("=" * 60)
    
    while True:
        pedestrian_time = input("🕒 Enter Pedestrian Signal time (HH:MM:SS): ")
        try:
            hour, minute, second = map(int, pedestrian_time.split(':'))
            if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                break
            else:
                print("❌ Invalid time values. Please use valid HH:MM:SS format.")
        except:
            print("❌ Invalid time format. Please use HH:MM:SS")
    
    print("📍 Connecting to Signal Manipulator Server...")
    
    try:
        success = server.register_client_time("Pedestrian Signal", pedestrian_time)
        if success:
            print("✅ Pedestrian Signal time registered successfully!")
        else:
            print("❌ Failed to register time")
            return False
        
        print("⏳ Waiting for Berkeley Algorithm synchronization...")
        time.sleep(2)

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

def pedestrian_signal_controller():
    """Monitor pedestrian crossing signals - only shows output when there are messages"""
    print("🚶‍♂️ Monitoring pedestrian crossing signals...")
    
    try:
        while True:
            msg = server.get_next_pedestrian_message()
            if msg is None:
                # Sleep briefly and check again, but don't print anything
                time.sleep(0.5)
                continue
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
    if not register_time_and_sync():
        print("❌ Failed to initialize. Exiting...")
        exit(1)
    
    print("\n" + "=" * 60)
    print("📍 Connected to Signal Manipulator Server")
    print("🔄 Pedestrian signals work opposite to vehicle signals")
    print("   - When vehicles at Junction 12 stop → Pedestrians at Junction 12 can cross")
    print("   - When vehicles at Junction 34 stop → Pedestrians at Junction 34 can cross")
    print("=" * 60)
    
    # Display status once at startup
    display_status()
    
    try:
        # Run the pedestrian signal controller - it will only output when there are actual messages
        pedestrian_signal_controller()
    except KeyboardInterrupt:
        print("\n🛑 Pedestrian signal monitor stopped manually.")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("🔄 Retrying connection...")
        time.sleep(5)