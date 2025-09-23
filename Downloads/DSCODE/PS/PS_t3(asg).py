import xmlrpc.client
import time

# Connect to server using its LAN IP (same server as vehicle signals)
server = xmlrpc.client.ServerProxy("http://192.168.1.100:8000/", allow_none=True)

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

def display_banner():
    print("=" * 60)
    print("🚶‍♂️ PEDESTRIAN CROSSING SIGNAL CONTROLLER 🚶‍♀️")
    print("=" * 60)
    print("📍 Connected to Signal Manipulator Server")
    print("🔄 Pedestrian signals work opposite to vehicle signals")
    print("   - When vehicles at Junction 12 stop → Pedestrians at Junction 12 can cross")
    print("   - When vehicles at Junction 34 stop → Pedestrians at Junction 34 can cross")
    print("=" * 60)

if __name__ == "__main__":
    display_banner()
    
    while True:
        try:
            # Wait for signal changes from the main controller
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