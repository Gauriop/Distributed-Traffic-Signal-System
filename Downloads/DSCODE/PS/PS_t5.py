import xmlrpc.client
import time

server = xmlrpc.client.ServerProxy("http://127.0.0.1:8000/", allow_none=True)

def register_time_and_sync():
    """Register this client's time and trigger Berkeley synchronization"""
    print("=" * 80)
    print("🚶‍♂️ FOUR-WAY PEDESTRIAN CONTROLLER - RICART-AGRAWALA 🚶‍♀️")
    print("⚡ MONITORING PEDESTRIAN CROSSINGS (OPPOSITE TO VEHICLE SIGNALS)")
    print("=" * 80)
    
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

def p_signal():
    """Monitor four-way pedestrian crossing signals"""
    print("🚶‍♂️ Monitoring four-way pedestrian crossing signals...")
    print("🔄 Pedestrian signals change when vehicle signals change (mutual exclusion)")
    print("⚡ When vehicle signal X turns GREEN → Pedestrian crossing X turns RED")
    print("⚡ When vehicle signal X turns RED → Pedestrian crossing X turns GREEN")
    print("🎯 KEY: Signal trying to turn GREEN = Pedestrian crossing turns RED")
    
    try:
        message_count = 0
        while True:
            msg = server.get_next_pedestrian_message()
            if msg is None:
                # Sleep briefly and check again, but don't print anything
                time.sleep(0.5)
                continue
            message_count += 1
            print(f"🚶‍♂️ PEDESTRIAN: {msg}")

    except Exception as e:
        print("❌ Error communicating with server:", e)

def display_status():
    """Display current synchronized time and signal status"""
    try:
        sync_time = server.get_synchronized_time()
        active_signal = server.get_active_signal()
        if sync_time:
            print(f"⏰ Current synchronized time: {sync_time}")
        if active_signal:
            print(f"🚗 Vehicle signal currently GREEN: {active_signal}")
            print(f"🚶‍♀️ Pedestrian crossing currently RED: {active_signal}")
            
            pedestrian_green = [sig for sig in [1, 2, 3, 4] if sig != active_signal]
            if pedestrian_green:
                print(f"🚶‍♂️ Pedestrian crossings currently GREEN: {pedestrian_green}")
    except Exception as e:
        print(f"❌ Status check failed: {e}")

if __name__ == "__main__":
    if not register_time_and_sync():
        print("❌ Failed to initialize. Exiting...")
        exit(1)
    
    print("\n" + "=" * 80)
    print("📍 Connected to Four-Way Signal Manipulator Server")
    print("🔄 PEDESTRIAN SIGNAL LOGIC (Opposite to Vehicle Signals):")
    print("   🟢 When Vehicle Signal X is RED  → Pedestrian Crossing X is GREEN")
    print("   🔴 When Vehicle Signal X is GREEN → Pedestrian Crossing X is RED")
    print("🔒 Ricart-Agrawala ensures coordinated signal changes")
    print("⚡ Only ONE vehicle signal GREEN at a time = THREE pedestrian crossings GREEN")
    print("=" * 80)
    
    # Display status once at startup
    display_status()
    
    try:
        # Run the pedestrian signal controller
        p_signal()
    except KeyboardInterrupt:
        print("\n🛑 Four-way pedestrian signal monitor stopped manually.")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("🔄 Retrying connection...")
        time.sleep(5)