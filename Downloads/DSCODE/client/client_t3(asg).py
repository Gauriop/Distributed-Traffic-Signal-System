import xmlrpc.client
import random
import time

# connect to server using its LAN IP
server = xmlrpc.client.ServerProxy("http://192.168.1.100:8000/", allow_none=True)

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

def display_banner():
    print("=" * 60)
    print("🚗 VEHICLE TRAFFIC SIGNAL CONTROLLER 🚙")
    print("=" * 60)
    print("📍 Connected to Signal Manipulator Server")
    print("🔄 Controls vehicle traffic signals at Junctions 12 and 34")
    print("=" * 60)

if __name__ == "__main__":
    display_banner()
    
    while True:
        try:
            signal_controller()
            print(f"\n⏳ Waiting before next cycle...\n")
            time.sleep(2)
        except KeyboardInterrupt:
            print("\n🛑 Vehicle signal controller stopped manually.")
            break