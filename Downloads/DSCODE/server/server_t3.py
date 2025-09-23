import time
from xmlrpc.server import SimpleXMLRPCServer

current_active = 12   # default start
current_sequence = [] # list of (delay, message) pairs
pedestrian_sequence = [] # list of (delay, message) pairs for pedestrians

def signal_manipulator(pair_to_turn_off):
    global current_active, current_sequence, pedestrian_sequence

    if pair_to_turn_off != current_active:
        current_sequence = [(0, f"⚠️ Junction {pair_to_turn_off} already OFF. No action.")]
        pedestrian_sequence = [(0, f"⚠️ Pedestrian crossing {pair_to_turn_off} already ON. No action.")]
        return True

    # build sequence with different delays
    other = 34 if pair_to_turn_off == 12 else 12
    current_active = other

    # Vehicle signal sequence (original)
    current_sequence = [
        (5, f"🟡 Junction {pair_to_turn_off} is now YELLOW."),        
        (3, f"🔴 Junction {pair_to_turn_off} is now RED. Vehicles must stop."),   
    ]
    
    # Pedestrian signal sequence (opposite logic)
    pedestrian_sequence = [
        (1, f"🔴 Pedestrian crossing {other} is now RED. Do not cross."),
        (1, f"🟢 Pedestrian crossing {pair_to_turn_off} is now GREEN. Safe to cross.")
    ]

    current_sequence.append(
        (1, f"🟢 Junction {other} is now GREEN. Vehicles can go.")
    )
    return True

def get_next_message():
    """Return the next message in sequence (with its delay) for vehicles."""
    global current_sequence
    if not current_sequence:
        return None
    delay, msg = current_sequence.pop(0)
    time.sleep(delay)  
    print(msg)         
    return msg        

def get_next_pedestrian_message():
    """Return the next message in sequence (with its delay) for pedestrians."""
    global pedestrian_sequence
    if not pedestrian_sequence:
        return None
    delay, msg = pedestrian_sequence.pop(0)
    time.sleep(delay)   
    print(msg)          
    return msg          

if __name__ == "__main__":
    server = SimpleXMLRPCServer(("127.0.0.1", 8000), allow_none=True)
    server.register_function(signal_manipulator, "signal_manipulator")
    server.register_function(get_next_message, "get_next_message")
    server.register_function(get_next_pedestrian_message, "get_next_pedestrian_message")
    print("🚦 Signal Manipulator Server is running on port 8000...")
    print("📍 Vehicle signals and pedestrian crossings are now supported!")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped manually.")