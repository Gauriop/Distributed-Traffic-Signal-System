import xmlrpc.client
import random
import time

# connect to server using its LAN IP
server = xmlrpc.client.ServerProxy("http://127.0.0.1:8000/", allow_none=True)

def register_time_and_sync():
    """Register this client's time and trigger Berkeley synchronization"""
    print("=" * 60)
    print("🚗 VEHICLE TRAFFIC SIGNAL CONTROLLER 🚙")
    print("=" * 60)
    
    # Get traffic signal time input
    while True:
        traffic_time = input("🕒 Enter Traffic Signal time (HH:MM:SS): ")
        try:
            # Validate format
            hour, minute, second = map(int, traffic_time.split(':'))
            if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                break
            else:
                print("❌ Invalid time values. Please use valid HH:MM:SS format.")
        except:
            print("❌ Invalid time format. Please use HH:MM:SS")
    
    print("📍 Connecting to Signal Manipulator Server...")
    
    try:
        # Register this client's time
        success = server.register_client_time("Traffic Signal", traffic_time)
        if success:
            print("✅ Traffic Signal time registered successfully!")
        else:
            print("❌ Failed to register time")
            return False
        
        # Wait a moment for other clients to connect
        print("⏳ Waiting for all clients to connect...")
        time.sleep(3)
        
        # Trigger Berkeley synchronization
        sync_time = server.berkeley_synchronization()
        if sync_time:
            print(f"\n🎯 FINAL SYNCHRONIZED TIME: {sync_time}")
            print("✅ All traffic systems are now synchronized!")
        else:
            print("⏳ Synchronization pending - waiting for all clients...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during time synchronization: {e}")
        return False

def signal_controller():
    active_pair = random.choice([12, 34])
    pair_to_turn_off = 34 if active_pair == 12 else 12

    print(f"\n✅ Active Junction: {active_pair}")
    print(f"🚦 Requesting to turn OFF Junction: {pair_to_turn_off}")
    print(f"🚶‍♂️ This will turn ON pedestrian crossing at Junction: {pair_to_turn_off}")

    try:
        # Tell server to prepare sequence
        server.signal_manipulator(pair_to_turn_off)

        # Fetch each message with its delay
        while True:
            msg = server.get_next_message()
            if msg is None:
                break
            print(f"🚗 VEHICLE: {msg}")

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
    print("🔄 Controls vehicle traffic signals at Junctions 12 and 34")
    print("=" * 60)
    
    while True:
        try:
            display_status()
            signal_controller()
            print(f"\n⏳ Waiting before next cycle...\n")
            time.sleep(2)
        except KeyboardInterrupt:
            print("\n🛑 Vehicle signal controller stopped manually.")
            break