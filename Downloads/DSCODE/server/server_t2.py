import time
from xmlrpc.server import SimpleXMLRPCServer

current_active = 12   # default start
current_sequence = [] # list of (delay, message) pairs

def signal_manipulator(pair_to_turn_off):
    global current_active, current_sequence

    if pair_to_turn_off != current_active:
        current_sequence = [(0, f"⚠️ Junction {pair_to_turn_off} already OFF. No action.")]
        return True

    # build sequence with different delays
    other = 34 if pair_to_turn_off == 12 else 12
    current_active = other

    current_sequence = [
        (5, f"🟡 Junction {pair_to_turn_off} is now YELLOW."),        
        (3, f"🔴 Junction {pair_to_turn_off} is now RED. Vehicles must stop."), 
        (1, f"🟢 Junction {other} is now GREEN. Vehicles can go.")   
    ]
    return True

def get_next_message():
    """Return the next message in sequence (with its delay)."""
    global current_sequence
    if not current_sequence:
        return None  # now allowed
    delay, msg = current_sequence.pop(0)
    time.sleep(delay)   # wait before showing this step
    print(msg)          # server prints
    return msg          # client prints too

if __name__ == "__main__":
    server = SimpleXMLRPCServer(("127.0.0.1", 8000), allow_none=True)
    server.register_function(signal_manipulator, "signal_manipulator")
    server.register_function(get_next_message, "get_next_message")
    print("🚦 Signal Manipulator Server is running on port 8000...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped manually.")
