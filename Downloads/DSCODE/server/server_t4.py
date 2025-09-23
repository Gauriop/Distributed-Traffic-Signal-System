import time
from xmlrpc.server import SimpleXMLRPCServer
from datetime import datetime, timedelta

current_active = 12   # default start
current_sequence = [] # list of (delay, message) pairs
pedestrian_sequence = [] # list of (delay, message) pairs for pedestrians

# Berkeley Algorithm variables
server_time = None
client_times = {}  # {client_id: time_value}
synchronized_time = None

def set_server_time(time_input):
    """Set the server's clock time (Signal Manipulator time)"""
    global server_time
    try:
        # Parse time input (format: HH:MM:SS)
        hour, minute, second = map(int, time_input.split(':'))
        server_time = datetime.now().replace(hour=hour, minute=minute, second=second, microsecond=0)
        print(f"🕒 Server time set to: {server_time.strftime('%H:%M:%S')}")
        return True
    except:
        return False

def register_client_time(client_id, time_input):
    """Register a client's clock time"""
    global client_times
    try:
        # Parse time input (format: HH:MM:SS)
        hour, minute, second = map(int, time_input.split(':'))
        client_time = datetime.now().replace(hour=hour, minute=minute, second=second, microsecond=0)
        client_times[client_id] = client_time
        print(f"🕒 {client_id} time registered: {client_time.strftime('%H:%M:%S')}")
        return True
    except:
        return False

def berkeley_synchronization():
    """Implement Berkeley Algorithm for time synchronization"""
    global server_time, client_times, synchronized_time
    
    if not server_time or len(client_times) < 2:
        return None
    
    print("\n🔄 Starting Berkeley Algorithm Synchronization...")
    print(f"📍 Server (Signal Manipulator): {server_time.strftime('%H:%M:%S')}")
    
    # Collect all times
    all_times = [server_time]
    for client_id, client_time in client_times.items():
        print(f"📍 {client_id}: {client_time.strftime('%H:%M:%S')}")
        all_times.append(client_time)
    
    # Calculate average time (Berkeley Algorithm)
    total_seconds = sum(t.hour * 3600 + t.minute * 60 + t.second for t in all_times)
    avg_seconds = total_seconds // len(all_times)
    
    hours = avg_seconds // 3600
    minutes = (avg_seconds % 3600) // 60
    seconds = avg_seconds % 60
    
    synchronized_time = datetime.now().replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
    
    print(f"\n⏰ SYNCHRONIZED TIME: {synchronized_time.strftime('%H:%M:%S')}")
    print("✅ Berkeley Algorithm completed successfully!")
    
    return synchronized_time.strftime('%H:%M:%S')

def get_synchronized_time():
    """Return the current synchronized time"""
    global synchronized_time
    if synchronized_time:
        return synchronized_time.strftime('%H:%M:%S')
    return None

def signal_manipulator(pair_to_turn_off):
    global current_active, current_sequence, pedestrian_sequence

    # Show synchronized time before signal operations
    if synchronized_time:
        sync_time_str = synchronized_time.strftime('%H:%M:%S')
        print(f"⏰ Operating at synchronized time: {sync_time_str}")

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
        (1, f"🟢 Junction {other} is now GREEN. Vehicles can go.")   
    ]
    
    # Pedestrian signal sequence (opposite logic)
    pedestrian_sequence = [
        (5, f"🟡 Pedestrian crossing {other} is now YELLOW. Prepare to stop."),
        (3, f"🔴 Pedestrian crossing {other} is now RED. Do not cross."),
        (1, f"🟢 Pedestrian crossing {pair_to_turn_off} is now GREEN. Safe to cross.")
    ]
    return True

def get_next_message():
    """Return the next message in sequence (with its delay) for vehicles."""
    global current_sequence
    if not current_sequence:
        return None
    delay, msg = current_sequence.pop(0)
    time.sleep(delay)   # wait before showing this step
    
    # Add synchronized time to message
    time_prefix = ""
    if synchronized_time:
        time_prefix = f"⏰ [{synchronized_time.strftime('%H:%M:%S')}] "
    
    full_msg = time_prefix + msg
    print(full_msg)          # server prints
    return full_msg          # client prints too

def get_next_pedestrian_message():
    """Return the next message in sequence (with its delay) for pedestrians."""
    global pedestrian_sequence
    if not pedestrian_sequence:
        return None
    delay, msg = pedestrian_sequence.pop(0)
    time.sleep(delay)   # wait before showing this step
    
    # Add synchronized time to message
    time_prefix = ""
    if synchronized_time:
        time_prefix = f"⏰ [{synchronized_time.strftime('%H:%M:%S')}] "
    
    full_msg = time_prefix + msg
    print(full_msg)          # server prints
    return full_msg          # client prints too

if __name__ == "__main__":
    print("=" * 60)
    print("🚦 SIGNAL MANIPULATOR SERVER WITH BERKELEY ALGORITHM 🕒")
    print("=" * 60)
    
    # Get server time input
    while True:
        server_time_input = input("🕒 Enter Signal Manipulator time (HH:MM:SS): ")
        if set_server_time(server_time_input):
            break
        else:
            print("❌ Invalid time format. Please use HH:MM:SS")
    
    print("📍 Waiting for client connections to register their times...")
    print("📍 Berkeley synchronization will start once all clients connect.")
    print("=" * 60)
    
    # Bind to all interfaces so client PCs can connect
    server = SimpleXMLRPCServer(("127.0.0.1", 8000), allow_none=True)
    server.register_function(signal_manipulator, "signal_manipulator")
    server.register_function(get_next_message, "get_next_message")
    server.register_function(get_next_pedestrian_message, "get_next_pedestrian_message")
    server.register_function(register_client_time, "register_client_time")
    server.register_function(berkeley_synchronization, "berkeley_synchronization")
    server.register_function(get_synchronized_time, "get_synchronized_time")
    
    print("🚦 Signal Manipulator Server is running on port 8000...")
    print("📍 Vehicle signals, pedestrian crossings, and time sync are supported!")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped manually.")