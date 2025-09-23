import time
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from datetime import datetime, timedelta
import threading
import random
import socket
import sys
from collections import defaultdict

# Enhanced request handler with timeout and error handling
class EnhancedXMLRPCRequestHandler(SimpleXMLRPCRequestHandler):
    """Enhanced request handler with timeout and better error handling"""
    timeout = 60
    
    def setup(self):
        """Setup with socket timeout"""
        try:
            SimpleXMLRPCRequestHandler.setup(self)
            self.request.settimeout(self.timeout)
        except Exception as e:
            print(f"⚠️ PRIMARY: Setup error for client connection: {e}")
    
    def handle(self):
        """Handle request with error catching"""
        try:
            SimpleXMLRPCRequestHandler.handle(self)
        except socket.timeout:
            print("⏱️ PRIMARY: Client request timed out")
        except ConnectionResetError:
            print("🔌 PRIMARY: Client connection reset")
        except Exception as e:
            print(f"💥 PRIMARY: Request handling error: {e}")

# PRIMARY SERVER - ENHANCED FOR LOAD BALANCING WITH ERROR HANDLING
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

# Ricart-Agrawala Algorithm variables with thread safety
logical_clock = 0
pending_requests = {}  # {request_id: (timestamp, requesting_client, requested_signal, is_vip)}
replies_received = {}  # {request_id: set of clients that replied}
request_queue = []
current_request_id = 0
lock = threading.RLock()  # Use RLock for nested locking
clients_in_system = set()  # Track connected clients
in_critical_section = None  # Which client is currently in critical section

# Enhanced tracking for multiple concurrent requests
active_requests = defaultdict(list)  # Track requests by signal
request_history = []  # Keep history of requests for analysis
failed_requests = []  # Track failed requests

# VIP Vehicle System
vip_requests = {}  # {request_id: (timestamp, signal, vip_count)}
vip_pending_queue = []  # Queue for VIP requests with priority

# Performance and error tracking
server_stats = {
    'total_processed': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'timeout_requests': 0,
    'vip_processed': 0,
    'start_time': time.time()
}

def safe_execute(func, *args, **kwargs):
    """Safely execute function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"⚠️ PRIMARY: Error in {func.__name__}: {e}")
        server_stats['failed_requests'] += 1
        return None

def increment_logical_clock():
    """Increment logical clock for Ricart-Agrawala with thread safety"""
    global logical_clock
    with lock:
        logical_clock += 1
        return logical_clock

def update_signal_status(signal_num, new_status):
    """Update the shared signal status array and notify all clients"""
    global signal_status
    
    try:
        with lock:
            if new_status == "green":
                # Only one traffic signal can be green at a time
                for i in range(1, 5):
                    signal_status[f"t{i}"] = "red"
                    signal_status[f"p{i}"] = "green"  # Pedestrians opposite to vehicles
                
                # Set requested signal to green
                signal_status[f"t{signal_num}"] = "green"
                signal_status[f"p{signal_num}"] = "red"  # Pedestrian crossing goes red
            
            print(f"📊 PRIMARY SERVER - SIGNAL STATUS UPDATED: {signal_status}")
            return True
    except Exception as e:
        print(f"❌ PRIMARY: Error updating signal status: {e}")
        return False

def get_signal_status():
    """Return current signal status array with error handling"""
    try:
        with lock:
            return dict(signal_status)  # Return copy to avoid reference issues
    except Exception as e:
        print(f"❌ PRIMARY: Error getting signal status: {e}")
        # Return safe default
        return {
            "t1": "green", "t2": "red", "t3": "red", "t4": "red",
            "p1": "red", "p2": "green", "p3": "green", "p4": "green"
        }

def set_server_time(time_input):
    """Set the server's clock time (Signal Manipulator time)"""
    global server_time
    try:
        hour, minute, second = map(int, time_input.split(':'))
        server_time = datetime.now().replace(hour=hour, minute=minute, second=second, microsecond=0)
        print(f"🕐 PRIMARY - Server time set to: {server_time.strftime('%H:%M:%S')}")
        return True
    except Exception as e:
        print(f"❌ PRIMARY: Error setting server time: {e}")
        return False

def register_client_time(client_id, time_input):
    """Register a client's clock time with error handling"""
    global client_times, clients_in_system
    try:
        with lock:
            hour, minute, second = map(int, time_input.split(':'))
            client_time = datetime.now().replace(hour=hour, minute=minute, second=second, microsecond=0)
            client_times[client_id] = client_time
            clients_in_system.add(client_id)
            print(f"🕐 PRIMARY - {client_id} time registered: {client_time.strftime('%H:%M:%S')}")
            return True
    except Exception as e:
        print(f"❌ PRIMARY: Error registering client time: {e}")
        return False

def berkeley_synchronization():
    """Implement Berkeley Algorithm for time synchronization with error handling"""
    global server_time, client_times, synchronized_time
    
    try:
        with lock:
            if not server_time or len(client_times) < 1:  # Allow sync with just server time
                return None
            
            print("\n🔄 PRIMARY - Starting Berkeley Algorithm Synchronization...")
            print(f"📊 PRIMARY Server (Signal Manipulator): {server_time.strftime('%H:%M:%S')}")
            
            all_times = [server_time]
            for client_id, client_time in client_times.items():
                print(f"📊 PRIMARY - {client_id}: {client_time.strftime('%H:%M:%S')}")
                all_times.append(client_time)

            total_seconds = sum(t.hour * 3600 + t.minute * 60 + t.second for t in all_times)
            avg_seconds = total_seconds // len(all_times)
            
            hours = avg_seconds // 3600
            minutes = (avg_seconds % 3600) // 60
            seconds = avg_seconds % 60
            
            synchronized_time = datetime.now().replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
            
            print(f"\n⏰ PRIMARY - SYNCHRONIZED TIME: {synchronized_time.strftime('%H:%M:%S')}")
            print("✅ PRIMARY - Berkeley Algorithm completed successfully!")
            
            return synchronized_time.strftime('%H:%M:%S')
    except Exception as e:
        print(f"❌ PRIMARY: Error in Berkeley synchronization: {e}")
        return None

def get_synchronized_time():
    """Return the current synchronized time with error handling"""
    try:
        global synchronized_time
        if synchronized_time:
            return synchronized_time.strftime('%H:%M:%S')
        return None
    except Exception as e:
        print(f"❌ PRIMARY: Error getting synchronized time: {e}")
        return None

def handle_vip_deadlock(vip_list):
    """Handle VIP deadlock scenarios with enhanced error handling"""
    global current_active_signal
    
    try:
        if len(vip_list) < 2:
            return vip_list  # No deadlock with single VIP
        
        print(f"⚠️ PRIMARY - VIP DEADLOCK DETECTED:")
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
            print(f"   📋 PRIMARY - DEADLOCK RESOLUTION CASE 1:")
            print(f"   ✅ VIP in route {current_active_signal} has priority (signal already GREEN)")
            print(f"   ⏳ Other VIPs queued by timestamp")
            
            # Sort others by timestamp (earlier timestamp = higher priority)
            other_vips.sort(key=lambda x: x[1])
            return active_signal_vips + other_vips
        
        # Case 2: Both VIP routes are RED - use timestamps
        else:
            print(f"   📋 PRIMARY - DEADLOCK RESOLUTION CASE 2:")
            print(f"   🕐 All VIP routes are RED - using timestamps to resolve")
            vip_list.sort(key=lambda x: x[1])  # Sort by timestamp
            
            for i, (route, timestamp) in enumerate(vip_list):
                print(f"   {i+1}. PRIMARY - VIP Route {route} (timestamp: {timestamp})")
            
            return vip_list
    except Exception as e:
        print(f"❌ PRIMARY: Error handling VIP deadlock: {e}")
        return vip_list  # Return original list if error

def submit_vip_requests(vip_data):
    """Submit VIP requests to the server with error handling"""
    global vip_pending_queue
    
    try:
        if not vip_data:
            return True
        
        with lock:
            print(f"\n🚨 PRIMARY - VIP VEHICLES DETECTED!")
            print(f"   📋 VIP Routes: {[vip[0] for vip in vip_data]}")
            print(f"   🚗 Total VIPs: {len(vip_data)}")
            
            # Handle VIP deadlock if multiple VIPs
            if len(vip_data) > 1:
                vip_data = handle_vip_deadlock(vip_data)
            
            # Add VIPs to pending queue with priority
            for route, timestamp in vip_data:
                vip_pending_queue.append((route, timestamp))
                print(f"   👑 PRIMARY - VIP added to priority queue: Route {route}")
            
            print(f"   ✅ PRIMARY - All VIP requests queued with HIGH PRIORITY")
            server_stats['total_processed'] += 1
            return True
    except Exception as e:
        print(f"❌ PRIMARY: Error submitting VIP requests: {e}")
        server_stats['failed_requests'] += 1
        return False

def request_critical_section(client_id, requested_signal, is_vip=False):
    """Ricart-Agrawala: Request access to critical section with enhanced error handling"""
    global current_request_id, pending_requests, replies_received, in_critical_section, active_requests, request_history, vip_requests
    
    try:
        # Check if already in critical section
        if in_critical_section and in_critical_section != client_id and not is_vip:
            print(f"🚫 PRIMARY - DENIED: {client_id} request for signal {requested_signal} - Critical section busy with {in_critical_section}")
            return None, None
        
        timestamp = increment_logical_clock()
        
        with lock:
            current_request_id += 1
            request_id = current_request_id
            
            # Enhanced logging for requests
            request_info = {
                'request_id': request_id,
                'timestamp': timestamp,
                'client_id': client_id,
                'requested_signal': requested_signal,
                'is_vip': is_vip,
                'time': datetime.now().strftime('%H:%M:%S.%f')[:-3],
                'server': 'PRIMARY'
            }
            request_history.append(request_info)
            active_requests[requested_signal].append(request_id)
            
            if is_vip:
                vip_requests[request_id] = (timestamp, requested_signal, 1)
                print(f"👑 PRIMARY - VIP REQUEST #{request_id}:")
                print(f"   🎯 VIP Route: {requested_signal}")
                print(f"   ⏰ Timestamp: {timestamp}")
                print(f"   🚨 PRIORITY: HIGH")
                server_stats['vip_processed'] += 1
            else:
                print(f"📋 PRIMARY - REGULAR REQUEST #{request_id}:")
                print(f"   👤 Client: {client_id}")
                print(f"   🎯 Signal: {requested_signal}")
                print(f"   ⏰ Timestamp: {timestamp}")
            
            pending_requests[request_id] = (timestamp, client_id, requested_signal, is_vip)
            replies_received[request_id] = set()
            server_stats['total_processed'] += 1
        
        return request_id, timestamp
    except Exception as e:
        print(f"❌ PRIMARY: Error requesting critical section: {e}")
        server_stats['failed_requests'] += 1
        return None, None

def send_reply(request_id, replying_client, can_reply=True):
    """Ricart-Agrawala: Send reply to a request with error handling"""
    global replies_received
    
    try:
        with lock:
            if request_id in replies_received and can_reply:
                replies_received[request_id].add(replying_client)
                return True
    except Exception as e:
        print(f"❌ PRIMARY: Error sending reply: {e}")
    return False

def can_enter_critical_section(request_id):
    """Check if client can enter critical section with VIP priority and error handling"""
    global pending_requests, replies_received, clients_in_system, in_critical_section
    
    try:
        with lock:
            if request_id not in pending_requests:
                return False
            
            timestamp, requesting_client, requested_signal, is_vip = pending_requests[request_id]
            
            # VIP requests get immediate priority
            if is_vip:
                print(f"👑 PRIMARY - VIP PRIORITY ACCESS GRANTED:")
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
                print(f"✅ PRIMARY - CRITICAL SECTION ACCESS GRANTED:")
                print(f"   🎫 Request ID: {request_id}")
                print(f"   👤 Client: {requesting_client}")  
                print(f"   🎯 Signal: {requested_signal}")
                return True
            
            return False
    except Exception as e:
        print(f"❌ PRIMARY: Error checking critical section access: {e}")
        return False

def enter_critical_section(request_id):
    """Enter critical section with error handling"""
    global in_critical_section, pending_requests
    
    try:
        with lock:
            if request_id in pending_requests:
                timestamp, client_id, requested_signal, is_vip = pending_requests[request_id]
                in_critical_section = client_id
                
                if is_vip:
                    print(f"👑 PRIMARY - VIP ENTERING CRITICAL SECTION:")
                    print(f"   🚨 VIP has exclusive access")
                    print(f"   🎯 Processing VIP route: {requested_signal}")
                else:
                    print(f"🔒 PRIMARY - ENTERING CRITICAL SECTION:")
                    print(f"   📋 Client {client_id} has exclusive access")
                    print(f"   🎯 Processing signal change: {requested_signal}")
                return True
    except Exception as e:
        print(f"❌ PRIMARY: Error entering critical section: {e}")
    return False

def exit_critical_section(request_id):
    """Exit critical section with error handling"""
    global in_critical_section, pending_requests, replies_received, active_requests, vip_requests
    
    try:
        with lock:
            if request_id in pending_requests and in_critical_section:
                timestamp, client_id, requested_signal, is_vip = pending_requests[request_id]
                
                if is_vip:
                    print(f"🎯 PRIMARY - VIP EXITING CRITICAL SECTION:")
                    print(f"   ✅ VIP route {requested_signal} completed")
                    print(f"   🔓 Critical section now available")
                    
                    # Clean up VIP request
                    if request_id in vip_requests:
                        del vip_requests[request_id]
                else:
                    print(f"🔓 PRIMARY - EXITING CRITICAL SECTION:")
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
                
                server_stats['successful_requests'] += 1
                return True
    except Exception as e:
        print(f"❌ PRIMARY: Error exiting critical section: {e}")
    return False

def signal_manipulator(requested_signal):
    """Handle regular signal changes with Ricart-Agrawala mutual exclusion and error handling"""
    global current_active_signal, current_sequence, pedestrian_sequence
    
    try:
        if synchronized_time:
            sync_time_str = synchronized_time.strftime('%H:%M:%S')
            print(f"⏰ PRIMARY - Operating at synchronized time: {sync_time_str}")
        
        # Determine client
        client_id = f"PRIMARY-Vehicle Controller (Thread-{threading.current_thread().ident % 1000})"
        
        # Create regular request
        request_id, timestamp = request_critical_section(client_id, requested_signal, is_vip=False)
        
        if request_id is None:
            current_sequence = [(0, f"⚠️ PRIMARY - Critical section busy. Request denied for signal {requested_signal}.")]
            return False
        
        # Simulate replies from other clients
        for client in clients_in_system:
            if client != client_id:
                send_reply(request_id, client, True)
        
        # Check if we can enter critical section
        if not can_enter_critical_section(request_id):
            current_sequence = [(0, f"⏳ PRIMARY - Waiting for critical section access for signal {requested_signal}...")]
            return False
        
        # Enter critical section
        if not enter_critical_section(request_id):
            current_sequence = [(0, f"❌ PRIMARY - Failed to enter critical section for signal {requested_signal}")]
            return False
        
        # Execute signal change
        result = execute_signal_change(requested_signal, request_id)
        exit_critical_section(request_id)
        
        return result
    except Exception as e:
        print(f"❌ PRIMARY: Error in signal_manipulator: {e}")
        server_stats['failed_requests'] += 1
        return False

def vip_signal_manipulator(requested_signal):
    """Handle VIP signal changes with highest priority and error handling"""
    global current_active_signal, current_sequence, pedestrian_sequence
    
    try:
        if synchronized_time:
            sync_time_str = synchronized_time.strftime('%H:%M:%S')
            print(f"⏰ PRIMARY - Operating at synchronized time: {sync_time_str}")
        
        # Determine VIP client
        client_id = f"PRIMARY-VIP-Controller-{requested_signal}"
        
        # Create VIP request with highest priority
        request_id, timestamp = request_critical_section(client_id, requested_signal, is_vip=True)
        
        if request_id is None:
            current_sequence = [(0, f"⚠️ PRIMARY - VIP request denied for signal {requested_signal}.")]
            return False
        
        # VIPs get immediate access - no need to wait for replies
        if not can_enter_critical_section(request_id):
            current_sequence = [(0, f"⏳ PRIMARY - VIP waiting for critical section access...")]
            return False
        
        # Enter critical section
        if not enter_critical_section(request_id):
            current_sequence = [(0, f"❌ PRIMARY - VIP failed to enter critical section for signal {requested_signal}")]
            return False
        
        # Execute signal change (same as regular)
        result = execute_signal_change(requested_signal, request_id)
        exit_critical_section(request_id)
        
        return result
    except Exception as e:
        print(f"❌ PRIMARY: Error in vip_signal_manipulator: {e}")
        server_stats['failed_requests'] += 1
        return False

def execute_signal_change(requested_signal, request_id):
    """Execute the actual signal change logic - SAME for VIP and regular with error handling"""
    global current_active_signal, current_sequence, pedestrian_sequence
    
    try:
        # Check if signal is already active
        if requested_signal == current_active_signal:
            current_sequence = [(0, f"ℹ️ PRIMARY - Signal {requested_signal} is already active (GREEN). No change needed.")]
            pedestrian_sequence = [(0, f"ℹ️ PRIMARY - Pedestrian crossing {requested_signal} already RED. No change needed.")]
            return True
        
        print(f"🚦 PRIMARY - EXECUTING SIGNAL CHANGE:")
        print(f"   🔄 Changing from signal {current_active_signal} to {requested_signal}")
        print(f"   📋 Mutual exclusion ensures atomic operation")
        
        old_signal = current_active_signal
        current_active_signal = requested_signal
        
        # Update the shared signal status array
        if not update_signal_status(requested_signal, "green"):
            print("⚠️ PRIMARY: Warning - Signal status update failed")
        
        # Create signal change sequence - IDENTICAL for VIP and regular
        current_sequence = []
        current_sequence.append((3, f"🟡 PRIMARY - Junction {old_signal} is now YELLOW."))
        current_sequence.append((2, f"🔴 PRIMARY - Junction {old_signal} is now RED. Vehicles must stop."))
        current_sequence.append((2, f"🟢 PRIMARY - Junction {requested_signal} is now GREEN. Vehicles can go."))
        
        # Pedestrian signals (opposite to vehicle signals) - IDENTICAL for VIP and regular
        pedestrian_sequence = []
        pedestrian_sequence.append((1, f"🟢 PRIMARY - Pedestrian crossing {old_signal} is now GREEN. Safe to cross."))
        pedestrian_sequence.append((1, f"🔴 PRIMARY - Pedestrian crossing {requested_signal} is now RED. Do not cross."))
        
        return True
    except Exception as e:
        print(f"❌ PRIMARY: Error executing signal change: {e}")
        return False

def get_next_message():
    """Return the next message in sequence (with its delay) for vehicles with error handling."""
    global current_sequence
    try:
        if not current_sequence:
            return None
        
        delay, msg = current_sequence.pop(0)
        if delay > 0:
            time.sleep(delay)  
        
        print(msg)          
        return msg
    except Exception as e:
        print(f"❌ PRIMARY: Error getting next message: {e}")
        return None

def get_next_pedestrian_message():
    """Return the next message in sequence (with its delay) for pedestrians with error handling."""
    global pedestrian_sequence
    try:
        if not pedestrian_sequence:
            return None
        
        delay, msg = pedestrian_sequence.pop(0)
        if delay > 0:
            time.sleep(delay)   

        print(msg)          
        return msg
    except Exception as e:
        print(f"❌ PRIMARY: Error getting next pedestrian message: {e}")
        return None

def get_active_signal():
    """Return currently active signal with error handling"""
    try:
        global current_active_signal
        return current_active_signal
    except Exception as e:
        print(f"❌ PRIMARY: Error getting active signal: {e}")
        return 1  # Default to signal 1

def get_system_stats():
    """Return comprehensive system statistics for monitoring with error handling"""
    global request_history, active_requests, current_active_signal, vip_requests, server_stats
    
    try:
        with lock:
            total_requests = len(request_history)
            vip_total = sum(1 for req in request_history if req.get('is_vip', False))
            pending_count = sum(len(requests) for requests in active_requests.values())
            vip_pending = len(vip_requests)
            uptime = time.time() - server_stats['start_time']
            
            stats = {
                'server_type': 'PRIMARY',
                'current_active_signal': current_active_signal,
                'total_requests_processed': total_requests,
                'vip_requests_processed': vip_total,
                'pending_requests': pending_count,
                'vip_pending_requests': vip_pending,
                'in_critical_section': in_critical_section,
                'active_requests_by_signal': dict(active_requests),
                'signal_status': dict(signal_status),
                'successful_requests': server_stats['successful_requests'],
                'failed_requests': server_stats['failed_requests'],
                'timeout_requests': server_stats['timeout_requests'],
                'uptime_seconds': uptime,
                'requests_per_minute': (total_requests / (uptime / 60)) if uptime > 0 else 0
            }
            
            return stats
    except Exception as e:
        print(f"❌ PRIMARY: Error getting system stats: {e}")
        return {
            'server_type': 'PRIMARY',
            'current_active_signal': 1,
            'total_requests_processed': 0,
            'error': str(e)
        }

if __name__ == "__main__":
    print("=" * 80)
    print("🟦 ENHANCED PRIMARY SERVER - FOUR-WAY INTERSECTION VIP PRIORITY SYSTEM")
    print("📡 RUNNING ON PORT 8000 (PRIMARY FOR LOAD BALANCING)")
    print("⚖️ WORKS WITH ENHANCED LOAD BALANCER ON PORT 9000")
    print("⚡ VIP VEHICLES GET HIGHER PRIORITY IN PROCESSING QUEUE!")
    print("🚨 VIP Deadlock Handling: Timestamp-based & Signal-state Resolution")
    print("🎯 TWO SEPARATE INPUTS: Regular signals + VIP vehicles")
    print("👑 VIPs processed first, then regular requests")
    print("📊 SHARED SIGNAL STATUS ARRAY: Real-time status updates")
    print("🛡️ ENHANCED ERROR HANDLING: Timeout, connection, XML-RPC faults")
    print("🔧 THREAD SAFETY: RLock protection for concurrent requests")
    print("📈 PERFORMANCE MONITORING: Request success/failure tracking")
    print("=" * 80)

    try:
        while True:
            server_time_input = input("🕐 Enter PRIMARY Signal Manipulator time (HH:MM:SS): ")
            if set_server_time(server_time_input):
                break
            else:
                print("❌ Invalid time format. Please use HH:MM:SS")
        
        print("📊 PRIMARY - Enhanced server starting with robust error handling...")
        print("📊 PRIMARY - Berkeley synchronization will start once clients connect.")
        print("📋 PRIMARY - Using Enhanced Ricart-Agrawala algorithm with VIP PRIORITY")
        print(f"🚦 PRIMARY - Four-way intersection: Signals 1, 2, 3, 4")
        print(f"🟢 PRIMARY - Currently active signal: {current_active_signal} (Only ONE can be GREEN)")
        print("👑 PRIMARY - VIP vehicles get priority processing!")
        print("🎲 PRIMARY - VIP generation: Manual control via manual_t8.py")
        print(f"📊 PRIMARY - Initial signal status: {signal_status}")
        print("⚖️ PRIMARY - Ready for load balancing with clone server!")
        print("🛡️ PRIMARY - Enhanced with timeout handling and error recovery!")
        print("=" * 80)
        
        # Create enhanced server with timeout handling
        server = SimpleXMLRPCServer(
            ("127.0.0.1", 8000), 
            allow_none=True,
            requestHandler=EnhancedXMLRPCRequestHandler
        )
        
        # Set server socket timeout
        server.socket.settimeout(60)
        server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Register functions with error handling wrappers
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
        
        print("👑 PRIMARY Enhanced VIP-Priority Four-Way Signal Server running on port 8000...")
        print("🚨 PRIMARY - Ready to handle VIP priority requests and deadlock resolution!")
        print("📊 PRIMARY - Signal status array synchronized across all clients!")
        print("⚖️ PRIMARY - Load balancing ready with clone server on port 8001!")
        print("🛡️ PRIMARY - Enhanced error handling and timeout management active!")
        print("🚀 PRIMARY - Ready for high-load testing scenarios!")
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 PRIMARY Enhanced Server stopped manually.")
        print("\n📈 PRIMARY - FINAL SYSTEM STATISTICS:")
        stats = get_system_stats()
        print(f"   PRIMARY - Total requests processed: {stats['total_requests_processed']}")
        print(f"   PRIMARY - Successful requests: {stats['successful_requests']}")
        print(f"   PRIMARY - Failed requests: {stats['failed_requests']}")
        print(f"   PRIMARY - VIP requests processed: {stats['vip_requests_processed']}")
        print(f"   PRIMARY - Final active signal: {stats['current_active_signal']}")
        print(f"   PRIMARY - Uptime: {stats['uptime_seconds']:.1f} seconds")
        if stats['uptime_seconds'] > 0:
            print(f"   PRIMARY - Requests per minute: {stats['requests_per_minute']:.2f}")
    except Exception as e:
        print(f"❌ PRIMARY Server error: {e}")
        print("💡 Check network settings and port availability")
    finally:
        print("🔄 PRIMARY Server shutdown complete.")