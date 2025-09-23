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

    try:
        # Tell server to prepare sequence
        server.signal_manipulator(pair_to_turn_off)

        # Fetch each message with its delay
        while True:
            msg = server.get_next_message()
            if msg is None:
                break
            print(msg)

    except Exception as e:
        print("❌ Error communicating with server:", e)

if __name__ == "__main__":
    while True:
        signal_controller()
        print(f"\n⏳ Waiting before next cycle...\n")
        time.sleep(2)
