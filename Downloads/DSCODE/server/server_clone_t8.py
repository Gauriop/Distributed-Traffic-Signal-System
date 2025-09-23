import time
from xmlrpc.server import SimpleXMLRPCServer
from datetime import datetime, timedelta
import threading
import random
from collections import defaultdict

# CLONE SERVER - IDENTICAL TO PRIMARY BUT ON PORT 8001
# Traffic signal state - Only ONE signal can be active at a time
current_active_signal = 1  # Initially signal 1 is active (GREEN)
current_sequence = [] 
pedestrian_sequence = [] 

# Shared signal status array - synchronized across all clients
signal_status = {
    "t1": "green",   # Traffic signal 1
    "t2": "red",     # Traffic signal 2
    "t3": "red",     # Traffic signal 3
    "t4": "red",     # Traffic signal 4
    "p1": "red",     # Pedestrian crossing 1
    "p2": "green",   # Pedestrian crossing 2
    "p3": "green",   # Pedestrian crossing 3
    "p4": "green"    # Pedestrian crossing 4
}

# Time synchronization
server_time = None
client_times = {}  
synchronized_time = None

# Ricart-Agrawala Algorithm variables
logical_clock = 0
pending_requests = {}  # {request_id: (timestamp, requesting_client, requested_signal, is_vip)}
replies_received = {}  # {request_id: set of clients that replied}
request_queue = []
current_request_id = 0
lock = threading.Lock()
clients_in_system = set()  # Track connected clients
in_critical_section = None  # Which client is currently in critical section

# Enhanced tracking for multiple concurrent requests
active_requests = defaultdict(list)  # Track requests by signal
request_history = []  # Keep history of requests for analysis

# VIP Vehicle System
vip_requests = {}  # {request_id: (timestamp, signal, vip_count)}
vip_pending_queue = []  # Queue for VIP requests with priority

def increment_logical_clock():
    """Increment logical clock for Ricart-Agrawala"""
    global logical_clock
    with lock:
        logical_clock += 1
        return logical_clock

def update_signal_status(signal_num, new_status):
    """Update the shared signal status array and notify all clients"""
    global signal_status
    
    if new_status == "green":
        # Only one traffic signal can be green at a time
        for i in range(1, 5):
            signal_status[f"t{i}"] = "red"
            signal_status[f"p{i}"] = "green"  # Pedestrians opposite to vehicles
        
        # Set requested signal to green
        signal_status[f"t{signal_num}"] = "green"
        signal_status[f"p{signal_num}"] = "red"  # Pedestrian crossing goes red
    
    print(f"🔄 CLONE SERVER - SIGNAL STATUS UPDATED: {signal_status}")

def get_signal_status():
    """Return current signal status array"""
    global signal_status
    return signal_status

def set_server_time(time_input):
    """Set the server's clock time (Signal Manipulator time)"""
    global server_time
    try:
        hour, minute, second = map(int, time_input.split(':'))
        server_time = datetime.now().replace(hour=hour, minute=minute, second=second, microsecond=0)
        print(f"🕐 CLONE - Server time set to: {server_time.strftime('%H:%M:%S')}")
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
        print(f"🕐 CLONE - {client_id} time registered: {client_time.strftime('%H:%M:%S')}")
        return True
    except:
        return False

def berkeley_synchronization():
    """Implement Berkeley Algorithm for time synchronization"""
    global server_time, client_times, synchronized_time
    
    if not server_time or len(client_times) < 2:
        return None
    
    print("\n🔄 CLONE - Starting Berkeley Algorithm Synchronization...")
    print(f"📊 CLONE Server (Signal Manipulator): {server_time.strftime('%H:%M:%S')}")
    
    all_times = [server_time]
    for client_id, client_time in client_times.items():
        print(f"📊 CLONE - {client_id}: {client_time.strftime('%H:%M:%S')}")
        all_times.append(client_time)

    total_seconds = sum(t.hour * 3600 + t.minute * 60 + t.second for t in all_times)
    avg_seconds = total_seconds // len(all_times)
    
    hours = avg_seconds // 3600
    minutes = (avg_seconds % 3600) // 60
    seconds = avg_seconds % 60
    
    synchronized_time = datetime.now().replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
    
    print(f"\n⏰ CLONE - SYNCHRONIZED TIME: {synchronized_time.strftime('%H:%M:%S')}")
    print("✅ CLONE - Berkeley Algorithm completed successfully!")
    
    return synchronized_time.strftime('%H:%M:%S')

def get_synchronized_time():
    """Return the current synchronized time"""
    global synchronized_time
    if synchronized_time:
        return synchronized_time.strftime('%H:%M:%S')
    return None

def handle_vip_deadlock(vip_list):
    """Handle VIP deadlock scenarios"""
    global current_active_signal
    
    if len(vip_list) < 2:
        return vip_list  # No deadlock with single VIP
    
    print(f"⚠️ CLONE - VIP DEADLOCK DETECTED:")
    print(f"   🚨 Multiple VIPs requesting different routes: {[vip[0] for vip in vip_list]}")
    
    # Separate VIPs based on current signal state
    active_signal_vips = []
    other_vips = []
    
    for route, timestamp in vip_list:
        if route == current_active_signal:
            active_signal_vips.append((route, timestamp))
        else:
            other_vips.append((route, timestamp))
    
    # Case 1: One VIP route is already GREEN
    if active_signal_vips:
        print(f"   🔋 CLONE - DEADLOCK RESOLUTION CASE 1:")
        print(f"   ✅ VIP in route {current_active_signal} has priority (signal already GREEN)")
        print(f"   ⏳ Other VIPs queued by timestamp")
        
        # Sort others by timestamp (earlier timestamp = higher priority)
        other_vips.sort(key=lambda x: x[1])
        return active_signal_vips + other_vips
    
    # Case 2: Both VIP routes are RED - use timestamps
    else:
        print(f"   🔋 CLONE - DEADLOCK RESOLUTION CASE 2:")
        print(f"   🕐 All VIP routes are RED - using timestamps to resolve")
        vip_list.sort(key=lambda x: x[1])  # Sort by timestamp
        
        for i, (route, timestamp) in enumerate(vip_list):
            print(f"   {i+1}. CLONE - VIP Route {route} (timestamp: {timestamp})")
        
        return vip_list

def submit_vip_requests(vip_data):
    """Submit VIP requests to the server"""
    global vip_pending_queue
    
    if not vip_data:
        return True
    
    print(f"\n🚨 CLONE - VIP VEHICLES DETECTED!")
    print(f"   📍 VIP Routes: {[vip[0] for vip in vip_data]}")
    print(f"   🚗 Total VIPs: {len(vip_data)}")
    
    # Handle VIP deadlock if multiple VIPs
    if len(vip_data) > 1:
        vip_data = handle_vip_deadlock(vip_data)
    
    # Add VIPs to pending queue with priority
    for route, timestamp in vip_data:
        vip_pending_queue.append((route, timestamp))
        print(f"   👑 CLONE - VIP added to priority queue: Route {route}")
    
    print(f"   ✅ CLONE - All VIP requests queued with HIGH PRIORITY")
    return True

def request_critical_section(client_id, requested_signal, is_vip=False):
    """Ricart-Agrawala: Request access to critical section"""
    global current_request_id, pending_requests, replies_received, in_critical_section, active_requests, request_history, vip_requests
    
    # Check if already in critical section
    if in_critical_section and in_critical_section != client_id and not is_vip:
        print(f"🚫 CLONE - DENIED: {client_id} request for signal {requested_signal} - Critical section busy with {in_critical_section}")
        return None, None
    
    timestamp = increment_logical_clock()
    current_request_id += 1
    request_id = current_request_id
    
    # Enhanced logging for requests
    request_info = {
        'request_id': request_id,
        'timestamp': timestamp,
        'client_id': client_id,
        'requested_signal': requested_signal,
        'is_vip': is_vip,
        'time': datetime.now().strftime('%H:%M:%S.%f')[:-3]
    }
    request_history.append(request_info)
    active_requests[requested_signal].append(request_id)
    
    if is_vip:
        vip_requests[request_id] = (timestamp, requested_signal, 1)
        print(f"👑 CLONE - VIP REQUEST #{request_id}:")
        print(f"   🎯 VIP Route: {requested_signal}")
        print(f"   ⏰ Timestamp: {timestamp}")
        print(f"   🚨 PRIORITY: HIGH")
    else:
        print(f"📋 CLONE - REGULAR REQUEST #{request_id}:")
        print(f"   👤 Client: {client_id}")
        print(f"   🎯 Signal: {requested_signal}")
        print(f"   ⏰ Timestamp: {timestamp}")
    
    with lock:
        pending_requests[request_id] = (timestamp, client_id, requested_signal, is_vip)
        replies_received[request_id] = set()
    
    return request_id, timestamp

def send_reply(request_id, replying_client, can_reply=True):
    """Ricart-Agrawala: Send reply to a request"""
    global replies_received
    
    with lock:
        if request_id in replies_received and can_reply:
            replies_received[request_id].add(replying_client)
            return True
    return False

def can_enter_critical_section(request_id):
    """Check if client can enter critical section with VIP priority"""
    global pending_requests, replies_received, clients_in_system, in_critical_section
    
    with lock:
        if request_id not in pending_requests:
            return False
        
        timestamp, requesting_client, requested_signal, is_vip = pending_requests[request_id]
        
        # VIP requests get immediate priority
        if is_vip:
            print(f"👑 CLONE - VIP PRIORITY ACCESS GRANTED:")
            print(f"   🎫 Request ID: {request_id}")
            print(f"   🚨 VIP Route: {requested_signal}")
            return True
        
        # Regular Ricart-Agrawala logic
        if in_critical_section:
            return False
            
        # Check if we have replies from all other clients
        other_clients = clients_in_system.copy()
        other_clients.discard(requesting_client)
        
        received_replies = replies_received[request_id]
        
        # For demonstration, simulate that all clients reply immediately
        if len(other_clients) <= len(received_replies) + 1:  # +1 for auto-replies
            print(f"✅ CLONE - CRITICAL SECTION ACCESS GRANTED:")
            print(f"   🎫 Request ID: {request_id}")
            print(f"   👤 Client: {requesting_client}")  
            print(f"   🎯 Signal: {requested_signal}")
            return True
        
        return False

def enter_critical_section(request_id):
    """Enter critical section"""
    global in_critical_section, pending_requests
    
    with lock:
        if request_id in pending_requests:
            timestamp, client_id, requested_signal, is_vip = pending_requests[request_id]
            in_critical_section = client_id
            
            if is_vip:
                print(f"👑 CLONE - VIP ENTERING CRITICAL SECTION:")
                print(f"   🚨 VIP has exclusive access")
                print(f"   🎯 Processing VIP route: {requested_signal}")
            else:
                print(f"🔒 CLONE - ENTERING CRITICAL SECTION:")
                print(f"   📋 Client {client_id} has exclusive access")
                print(f"   🎯 Processing signal change: {requested_signal}")
            return True
    return False

def exit_critical_section(request_id):
    """Exit critical section"""
    global in_critical_section, pending_requests, replies_received, active_requests, vip_requests
    
    with lock:
        if request_id in pending_requests and in_critical_section:
            timestamp, client_id, requested_signal, is_vip = pending_requests[request_id]
            
            if is_vip:
                print(f"🎯 CLONE - VIP EXITING CRITICAL SECTION:")
                print(f"   ✅ VIP route {requested_signal} completed")
                print(f"   🔓 Critical section now available")
                
                # Clean up VIP request
                if request_id in vip_requests:
                    del vip_requests[request_id]
            else:
                print(f"🔓 CLONE - EXITING CRITICAL SECTION:")
                print(f"   ✅ Signal change to {requested_signal} completed")
                print(f"   🔓 Critical section now available")
            
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
            
            return True
    return False

def signal_manipulator(requested_signal):
    """Handle regular signal changes with Ricart-Agrawala mutual exclusion"""
    global current_active_signal, current_sequence, pedestrian_sequence
    
    if synchronized_time:
        sync_time_str = synchronized_time.strftime('%H:%M:%S')
        print(f"⏰ CLONE - Operating at synchronized time: {sync_time_str}")
    
    # Determine client
    client_id = f"CLONE-Vehicle Controller (Thread-{threading.current_thread().ident % 1000})"
    
    # Create regular request
    request_id, timestamp = request_critical_section(client_id, requested_signal, is_vip=False)
    
    if request_id is None:
        current_sequence = [(0, f"⚠️ CLONE - Critical section busy. Request denied for signal {requested_signal}.")]
        return False
    
    # Simulate replies from other clients
    for client in clients_in_system:
        if client != client_id:
            send_reply(request_id, client, True)
    
    # Check if we can enter critical section
    if not can_enter_critical_section(request_id):
        current_sequence = [(0, f"⏳ CLONE - Waiting for critical section access for signal {requested_signal}...")]
        return False
    
    # Enter critical section
    if not enter_critical_section(request_id):
        current_sequence = [(0, f"❌ CLONE - Failed to enter critical section for signal {requested_signal}")]
        return False
    
    # Execute signal change
    result = execute_signal_change(requested_signal, request_id)
    exit_critical_section(request_id)
    
    return result

def vip_signal_manipulator(requested_signal):
    """Handle VIP signal changes with highest priority"""
    global current_active_signal, current_sequence, pedestrian_sequence
    
    if synchronized_time:
        sync_time_str = synchronized_time.strftime('%H:%M:%S')
        print(f"⏰ CLONE - Operating at synchronized time: {sync_time_str}")
    
    # Determine VIP client
    client_id = f"CLONE-VIP-Controller-{requested_signal}"
    
    # Create VIP request with highest priority
    request_id, timestamp = request_critical_section(client_id, requested_signal, is_vip=True)
    
    if request_id is None:
        current_sequence = [(0, f"⚠️ CLONE - VIP request denied for signal {requested_signal}.")]
        return False
    
    # VIPs get immediate access - no need to wait for replies
    if not can_enter_critical_section(request_id):
        current_sequence = [(0, f"⏳ CLONE - VIP waiting for critical section access...")]
        return False
    
    # Enter critical section
    if not enter_critical_section(request_id):
        current_sequence = [(0, f"❌ CLONE - VIP failed to enter critical section for signal {requested_signal}")]
        return False
    
    # Execute signal change (same as regular)
    result = execute_signal_change(requested_signal, request_id)
    exit_critical_section(request_id)
    
    return result

def execute_signal_change(requested_signal, request_id):
    """Execute the actual signal change logic - SAME for VIP and regular"""
    global current_active_signal, current_sequence, pedestrian_sequence
    
    # Check if signal is already active
    if requested_signal == current_active_signal:
        current_sequence = [(0, f"ℹ️ CLONE - Signal {requested_signal} is already active (GREEN). No change needed.")]
        pedestrian_sequence = [(0, f"ℹ️ CLONE - Pedestrian crossing {requested_signal} already RED. No change needed.")]
        return True
    
    print(f"🚦 CLONE - EXECUTING SIGNAL CHANGE:")
    print(f"   🔄 Changing from signal {current_active_signal} to {requested_signal}")
    print(f"   📋 Mutual exclusion ensures atomic operation")
    
    old_signal = current_active_signal
    current_active_signal = requested_signal
    
    # Update the shared signal status array
    update_signal_status(requested_signal, "green")
    
    # Create signal change sequence - IDENTICAL for VIP and regular
    current_sequence = []
    current_sequence.append((3, f"🟡 CLONE - Junction {old_signal} is now YELLOW."))
    current_sequence.append((2, f"🔴 CLONE - Junction {old_signal} is now RED. Vehicles must stop."))
    current_sequence.append((2, f"🟢 CLONE - Junction {requested_signal} is now GREEN. Vehicles can go."))
    
    # Pedestrian signals (opposite to vehicle signals) - IDENTICAL for VIP and regular
    pedestrian_sequence = []
    pedestrian_sequence.append((1, f"🟢 CLONE - Pedestrian crossing {old_signal} is now GREEN. Safe to cross."))
    pedestrian_sequence.append((1, f"🔴 CLONE - Pedestrian crossing {requested_signal} is now RED. Do not cross."))
    
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
    global request_history, active_requests, current_active_signal, vip_requests
    
    total_requests = len(request_history)
    vip_total = sum(1 for req in request_history if req.get('is_vip', False))
    pending_count = sum(len(requests) for requests in active_requests.values())
    vip_pending = len(vip_requests)
    
    stats = {
        'server_type': 'CLONE',
        'current_active_signal': current_active_signal,
        'total_requests_processed': total_requests,
        'vip_requests_processed': vip_total,
        'pending_requests': pending_count,
        'vip_pending_requests': vip_pending,
        'in_critical_section': in_critical_section,
        'active_requests_by_signal': dict(active_requests),
        'signal_status': signal_status
    }
    
    return stats

if __name__ == "__main__":
    print("=" * 80)
    print("🔄 CLONE SERVER - FOUR-WAY INTERSECTION VIP PRIORITY SYSTEM")
    print("📡 RUNNING ON PORT 8001 (CLONE OF PRIMARY SERVER)")
    print("⚡ VIP VEHICLES GET HIGHER PRIORITY IN PROCESSING QUEUE!")
    print("🚨 VIP Deadlock Handling: Timestamp-based & Signal-state Resolution")
    print("🎯 TWO SEPARATE INPUTS: Regular signals + VIP vehicles")
    print("👑 VIPs processed first, then regular requests")
    print("📊 SHARED SIGNAL STATUS ARRAY: Real-time status updates")
    print("=" * 80)

    while True:
        server_time_input = input("🕐 Enter CLONE Signal Manipulator time (HH:MM:SS): ")
        if set_server_time(server_time_input):
            break
        else:
            print("❌ Invalid time format. Please use HH:MM:SS")
    
    print("📊 CLONE - Waiting for client connections to register their times...")
    print("📊 CLONE - Berkeley synchronization will start once all clients connect.")
    print("📋 CLONE - Using Enhanced Ricart-Agrawala algorithm with VIP PRIORITY")
    print(f"🚦 CLONE - Four-way intersection: Signals 1, 2, 3, 4")
    print(f"🟢 CLONE - Currently active signal: {current_active_signal} (Only ONE can be GREEN)")
    print("👑 CLONE - VIP vehicles get priority processing!")
    print("🎲 CLONE - VIP generation: Manual control via manual_t7.py")
    print(f"📊 CLONE - Initial signal status: {signal_status}")
    print("=" * 80)
    
    server = SimpleXMLRPCServer(("127.0.0.1", 8001), allow_none=True)
    server.register_function(signal_manipulator, "signal_manipulator")
    server.register_function(vip_signal_manipulator, "vip_signal_manipulator")
    server.register_function(submit_vip_requests, "submit_vip_requests")
    server.register_function(get_next_message, "get_next_message")
    server.register_function(get_next_pedestrian_message, "get_next_pedestrian_message")
    server.register_function(register_client_time, "register_client_time")
    server.register_function(berkeley_synchronization, "berkeley_synchronization")
    server.register_function(get_synchronized_time, "get_synchronized_time")
    server.register_function(get_active_signal, "get_active_signal")
    server.register_function(get_system_stats, "get_system_stats")
    server.register_function(get_signal_status, "get_signal_status")
    
    print("👑 CLONE VIP-Priority Four-Way Signal Server running on port 8001...")
    print("🚨 CLONE - Ready to handle VIP priority requests and deadlock resolution!")
    print("📊 CLONE - Signal status array synchronized across all clients!")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 CLONE Server stopped manually.")
        print("\n📈 CLONE - FINAL SYSTEM STATISTICS:")
        stats = get_system_stats()
        print(f"   CLONE - Total requests processed: {stats['total_requests_processed']}")
        print(f"   CLONE - VIP requests processed: {stats['vip_requests_processed']}")
        print(f"   CLONE - Final active signal: {stats['current_active_signal']}")
        print(f"   CLONE - Final signal status: {stats['signal_status']}")