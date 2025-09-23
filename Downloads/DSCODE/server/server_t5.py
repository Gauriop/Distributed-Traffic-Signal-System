import time
from xmlrpc.server import SimpleXMLRPCServer
from datetime import datetime, timedelta
import threading
import random
from collections import defaultdict

# Traffic signal state - Only ONE signal can be active at a time
current_active_signal = 1  # Initially signal 1 is active (GREEN)
current_sequence = [] 
pedestrian_sequence = [] 

# Time synchronization
server_time = None
client_times = {}  
synchronized_time = None

# Ricart-Agrawala Algorithm variables
logical_clock = 0
pending_requests = {}  # {request_id: (timestamp, requesting_client, requested_signal)}
replies_received = {}  # {request_id: set of clients that replied}
request_queue = []
current_request_id = 0
lock = threading.Lock()
clients_in_system = set()  # Track connected clients
in_critical_section = None  # Which client is currently in critical section

# Enhanced tracking for multiple concurrent requests
active_requests = defaultdict(list)  # Track requests by signal
request_history = []  # Keep history of requests for analysis

def increment_logical_clock():
    """Increment logical clock for Ricart-Agrawala"""
    global logical_clock
    with lock:
        logical_clock += 1
        return logical_clock

def set_server_time(time_input):
    """Set the server's clock time (Signal Manipulator time)"""
    global server_time
    try:
        hour, minute, second = map(int, time_input.split(':'))
        server_time = datetime.now().replace(hour=hour, minute=minute, second=second, microsecond=0)
        print(f"🕐 Server time set to: {server_time.strftime('%H:%M:%S')}")
        return True
    except:
        return False

def register_client_time(client_id, time_input):
    """Register a client's clock time"""
    global client_times, clients_in_system
    try:
        hour, minute, second = map(int, time_input.split(':'))
        client_time = datetime.now().replace(hour=hour, minute=minute, second=second, microsecond=0)
        client_times[client_id] = client_time
        clients_in_system.add(client_id)
        print(f"🕐 {client_id} time registered: {client_time.strftime('%H:%M:%S')}")
        return True
    except:
        return False

def berkeley_synchronization():
    """Implement Berkeley Algorithm for time synchronization"""
    global server_time, client_times, synchronized_time
    
    if not server_time or len(client_times) < 2:
        return None
    
    print("\n🔄 Starting Berkeley Algorithm Synchronization...")
    print(f"📊 Server (Signal Manipulator): {server_time.strftime('%H:%M:%S')}")
    
    all_times = [server_time]
    for client_id, client_time in client_times.items():
        print(f"📊 {client_id}: {client_time.strftime('%H:%M:%S')}")
        all_times.append(client_time)

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

def request_critical_section(client_id, requested_signal):
    """Ricart-Agrawala: Request access to critical section"""
    global current_request_id, pending_requests, replies_received, in_critical_section, active_requests, request_history
    
    # Check if already in critical section
    if in_critical_section and in_critical_section != client_id:
        print(f"🚫 DENIED: {client_id} request for signal {requested_signal} - Critical section busy with {in_critical_section}")
        return None, None
    
    timestamp = increment_logical_clock()
    current_request_id += 1
    request_id = current_request_id
    
    # Enhanced logging for multiple requests
    request_info = {
        'request_id': request_id,
        'timestamp': timestamp,
        'client_id': client_id,
        'requested_signal': requested_signal,
        'time': datetime.now().strftime('%H:%M:%S.%f')[:-3]
    }
    request_history.append(request_info)
    active_requests[requested_signal].append(request_id)
    
    print(f"🔐 RICART-AGRAWALA REQUEST #{request_id}:")
    print(f"   👤 Client: {client_id}")
    print(f"   🎯 Signal: {requested_signal}")
    print(f"   ⏰ Timestamp: {timestamp}")
    print(f"   📊 Active requests for signal {requested_signal}: {len(active_requests[requested_signal])}")
    
    # Show concurrent requests if any
    total_active = sum(len(requests) for requests in active_requests.values())
    if total_active > 1:
        print(f"   ⚠️  CONCURRENT REQUESTS DETECTED: {total_active} total requests pending")
        for signal, req_list in active_requests.items():
            if req_list:
                print(f"      Signal {signal}: {len(req_list)} requests")
    
    with lock:
        pending_requests[request_id] = (timestamp, client_id, requested_signal)
        replies_received[request_id] = set()
    
    return request_id, timestamp

def send_reply(request_id, replying_client, can_reply=True):
    """Ricart-Agrawala: Send reply to a request"""
    global replies_received
    
    with lock:
        if request_id in replies_received and can_reply:
            replies_received[request_id].add(replying_client)
            print(f"📝 Reply: {replying_client} → Request #{request_id}")
            return True
    return False

def can_enter_critical_section(request_id):
    """Check if client can enter critical section"""
    global pending_requests, replies_received, clients_in_system, in_critical_section
    
    with lock:
        if request_id not in pending_requests or in_critical_section:
            return False
            
        # Check if we have replies from all other clients
        other_clients = clients_in_system.copy()
        timestamp, requesting_client, requested_signal = pending_requests[request_id]
        other_clients.discard(requesting_client)
        
        received_replies = replies_received[request_id]
        
        # For demonstration, simulate that all clients reply immediately
        # In a real distributed system, you'd wait for actual network replies
        if len(other_clients) <= len(received_replies) + 1:  # +1 for auto-replies
            print(f"✅ CRITICAL SECTION ACCESS GRANTED:")
            print(f"   🎫 Request ID: {request_id}")
            print(f"   👤 Client: {requesting_client}")  
            print(f"   🎯 Signal: {requested_signal}")
            return True
        
        print(f"⏳ Waiting for more replies for request #{request_id}...")
        return False

def enter_critical_section(request_id):
    """Enter critical section"""
    global in_critical_section, pending_requests
    
    with lock:
        if request_id in pending_requests:
            _, client_id, requested_signal = pending_requests[request_id]
            in_critical_section = client_id
            print(f"🏁 ENTERING CRITICAL SECTION:")
            print(f"   🔒 Client {client_id} has exclusive access")
            print(f"   🎯 Processing signal change: {requested_signal}")
            print(f"   ⚠️  All other requests must wait...")
            return True
    return False

def exit_critical_section(request_id):
    """Exit critical section"""
    global in_critical_section, pending_requests, replies_received, active_requests
    
    with lock:
        if request_id in pending_requests and in_critical_section:
            _, client_id, requested_signal = pending_requests[request_id]
            print(f"🔓 EXITING CRITICAL SECTION:")
            print(f"   ✅ Client {client_id} completed signal change to {requested_signal}")
            print(f"   🆓 Critical section now available for other requests")
            
            in_critical_section = None
            
            # Clean up this request
            del pending_requests[request_id]
            if request_id in replies_received:
                del replies_received[request_id]
            
            # Remove from active requests
            if requested_signal in active_requests:
                if request_id in active_requests[requested_signal]:
                    active_requests[requested_signal].remove(request_id)
                if not active_requests[requested_signal]:
                    del active_requests[requested_signal]
            
            # Show remaining pending requests
            remaining = sum(len(requests) for requests in active_requests.values())
            if remaining > 0:
                print(f"   📋 {remaining} requests still pending")
                for signal, req_list in active_requests.items():
                    if req_list:
                        print(f"      Signal {signal}: {len(req_list)} requests waiting")
            
            return True
    return False

def signal_manipulator(requested_signal):
    """Handle signal changes with Ricart-Agrawala mutual exclusion"""
    global current_active_signal, current_sequence, pedestrian_sequence
    
    if synchronized_time:
        sync_time_str = synchronized_time.strftime('%H:%M:%S')
        print(f"⏰ Operating at synchronized time: {sync_time_str}")
    
    # Determine client (in real system this would be passed as parameter)
    client_id = f"Vehicle Controller (Thread-{threading.current_thread().ident % 1000})"
    
    # Ricart-Agrawala: Request critical section
    request_id, timestamp = request_critical_section(client_id, requested_signal)
    
    if request_id is None:
        current_sequence = [(0, f"⚠️ Critical section busy. Request denied for signal {requested_signal}.")]
        return False
    
    # Simulate replies from other clients
    for client in clients_in_system:
        if client != client_id:
            send_reply(request_id, client, True)
    
    # Check if we can enter critical section
    if not can_enter_critical_section(request_id):
        current_sequence = [(0, f"⏳ Waiting for critical section access for signal {requested_signal}...")]
        return False
    
    # Enter critical section
    if not enter_critical_section(request_id):
        current_sequence = [(0, f"❌ Failed to enter critical section for signal {requested_signal}")]
        return False
    
    # Check if signal is already active
    if requested_signal == current_active_signal:
        current_sequence = [(0, f"ℹ️ Signal {requested_signal} is already active (GREEN). No change needed.")]
        pedestrian_sequence = [(0, f"ℹ️ Pedestrian crossing {requested_signal} already RED. No change needed.")]
        exit_critical_section(request_id)
        return True
    
    print(f"🚦 EXECUTING SIGNAL CHANGE IN CRITICAL SECTION:")
    print(f"   🔄 Changing from signal {current_active_signal} to signal {requested_signal}")
    print(f"   🔒 Mutual exclusion ensures atomic operation")
    
    old_signal = current_active_signal
    current_active_signal = requested_signal
    
    # Create signal change sequence
    current_sequence = []
    
    # Phase 1: Turn current signal to YELLOW then RED
    current_sequence.append((3, f"🟡 Junction {old_signal} is now YELLOW."))
    current_sequence.append((2, f"🔴 Junction {old_signal} is now RED. Vehicles must stop."))
    
    # Phase 2: Turn new signal to GREEN
    current_sequence.append((2, f"🟢 Junction {requested_signal} is now GREEN. Vehicles can go."))
    
    # Pedestrian signals (opposite to vehicle signals)
    pedestrian_sequence = []
    pedestrian_sequence.append((1, f"🟢 Pedestrian crossing {old_signal} is now GREEN. Safe to cross."))
    pedestrian_sequence.append((1, f"🔴 Pedestrian crossing {requested_signal} is now RED. Do not cross."))
    
    # Exit critical section
    exit_critical_section(request_id)
    
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

def get_active_signal():
    """Return currently active signal"""
    global current_active_signal
    return current_active_signal

def get_system_stats():
    """Return system statistics for monitoring"""
    global request_history, active_requests, current_active_signal
    
    total_requests = len(request_history)
    pending_count = sum(len(requests) for requests in active_requests.values())
    
    stats = {
        'current_active_signal': current_active_signal,
        'total_requests_processed': total_requests,
        'pending_requests': pending_count,
        'in_critical_section': in_critical_section,
        'active_requests_by_signal': dict(active_requests)
    }
    
    return stats

if __name__ == "__main__":
    print("=" * 80)
    print("🚦 FOUR-WAY INTERSECTION - ENHANCED RICART-AGRAWALA MUTUAL EXCLUSION 🔐")
    print("⚡ SUPPORTS MULTIPLE CONCURRENT REQUESTS - ONLY ONE SIGNAL GREEN AT A TIME!")
    print("🏁 DEMONSTRATES RACE CONDITIONS AND MUTUAL EXCLUSION")
    print("=" * 80)

    while True:
        server_time_input = input("🕐 Enter Signal Manipulator time (HH:MM:SS): ")
        if set_server_time(server_time_input):
            break
        else:
            print("❌ Invalid time format. Please use HH:MM:SS")
    
    print("📊 Waiting for client connections to register their times...")
    print("📊 Berkeley synchronization will start once all clients connect.")
    print("🔐 Using Enhanced Ricart-Agrawala algorithm for MUTUAL EXCLUSION")
    print(f"🚦 Four-way intersection: Signals 1, 2, 3, 4")
    print(f"🟢 Currently active signal: {current_active_signal} (Only ONE can be GREEN)")
    print("🎯 Ready to handle multiple concurrent requests!")
    print("=" * 80)
    
    server = SimpleXMLRPCServer(("127.0.0.1", 8000), allow_none=True)
    server.register_function(signal_manipulator, "signal_manipulator")
    server.register_function(get_next_message, "get_next_message")
    server.register_function(get_next_pedestrian_message, "get_next_pedestrian_message")
    server.register_function(register_client_time, "register_client_time")
    server.register_function(berkeley_synchronization, "berkeley_synchronization")
    server.register_function(get_synchronized_time, "get_synchronized_time")
    server.register_function(get_active_signal, "get_active_signal")
    server.register_function(get_system_stats, "get_system_stats")
    
    print("🚦 Enhanced Four-Way Signal Server with Ricart-Agrawala running on port 8000...")
    print("🔐 Ready to handle concurrent requests and ensure mutual exclusion!")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped manually.")
        print("\n📈 FINAL SYSTEM STATISTICS:")
        stats = get_system_stats()
        print(f"   Total requests processed: {stats['total_requests_processed']}")
        print(f"   Final active signal: {stats['current_active_signal']}")
        if stats['pending_requests'] > 0:
            print(f"   Requests pending at shutdown: {stats['pending_requests']}")