# vehicle_client.py
import xmlrpc.client
import random

# Connect to Signal Manipulator
server = xmlrpc.client.ServerProxy("http://localhost:8000/")

def signal_controller():
    active_pair = random.choice([12, 34])
    pair_to_turn_off = 34 if active_pair == 12 else 12

    print(f"✅ Active Junction: {active_pair}")
    print(f"🚦 Turning OFF Junction: {pair_to_turn_off}")

    # Get response including pedestrian signals
    response = server.signal_manipulator(pair_to_turn_off)

    print("\n📩 Full Response (Vehicles + Pedestrians):")
    for msg in response:
        print(msg)

signal_controller()
