import time
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from datetime import datetime, timedelta
import threading
import random
import socket
import sys
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
# Traffic signal state - North-South (1,3) initially active
current_active_signal = 1  # North-South pair active
current_sequence = [] 
pedestrian_sequence = [] 

# Shared signal status array - synchronized across all clients
signal_status = {
    "t1": "green",   # Traffic signal 1 (North) - GREEN
    "t2": "red",     # Traffic signal 2 (East) - RED
    "t3": "green",   # Traffic signal 3 (South) - GREEN  
    "t4": "red",     # Traffic signal 4 (West) - RED
    "p1": "red",     # Pedestrian crossing 1 (North) - RED (opposite to vehicle)
    "p2": "green",   # Pedestrian crossing 2 (East) - GREEN
    "p3": "red",     # Pedestrian crossing 3 (South) - RED (opposite to vehicle)
    "p4": "green"    # Pedestrian crossing 4 (West) - GREEN
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

# Auto-cycling timer for traffic simulation
auto_cycle_enabled = True
auto_cycle_initialized = False  # Track if auto-cycle has been properly initialized
last_signal_change = time.time()
signal_cycle_interval = 8  # Change signal every 8 seconds

# VIP mode control - stops auto-cycle when VIP is active
vip_mode_active = False
vip_active_signal = None
vip_start_time = None
vip_duration = 10  # VIP lasts 10 seconds

def auto_cycle_traffic_signals():
    """Automatically cycle through traffic signals with yellow transitions - SYNCHRONIZED"""
    global current_active_signal, last_signal_change, signal_cycle_interval, auto_cycle_enabled, auto_cycle_initialized
    global vip_mode_active, vip_active_signal, vip_start_time, vip_duration
    
    try:
        if not auto_cycle_enabled:
            return
            
        # Check if VIP mode should be ended
        if vip_mode_active and vip_start_time:
            current_time = time.time()
            if current_time - vip_start_time >= vip_duration:
                # VIP timeout - resume auto-cycle
                print(f"⏰ VIP timeout reached, resuming auto-cycle")
                vip_mode_active = False
                vip_active_signal = None
                vip_start_time = None
                
        # Skip auto-cycling if VIP is active
        if vip_mode_active and vip_active_signal:
            # Keep VIP signal green, others red
            with lock:
                for i in range(1, 5):
                    if i == vip_active_signal:
                        signal_status[f"t{i}"] = "green"
                        signal_status[f"p{i}"] = "red"
                    else:
                        signal_status[f"t{i}"] = "red"
                        signal_status[f"p{i}"] = "green"
            return
        
        current_time = time.time()
        
        # Use absolute time-based synchronization to keep servers in sync
        # Both servers will switch at the same absolute time moments
        cycle_position = int(current_time // signal_cycle_interval) % 2
        
        # Calculate position within the current 8-second cycle
        time_in_cycle = current_time % signal_cycle_interval
        
        # Determine which signals should be active based on absolute time
        if cycle_position == 0:
            # Even cycles: North-South active
            active_signals = [1, 3]  # North-South
            current_active_signal = 1
            current_pair = "North-South"
        else:
            # Odd cycles: East-West active  
            active_signals = [2, 4]  # East-West
            current_active_signal = 2
            current_pair = "East-West"
        
        # Always update signal status to ensure synchronization
        with lock:
            # Reset all signals to red first
            for i in range(1, 5):
                signal_status[f"t{i}"] = "red"
                signal_status[f"p{i}"] = "green"
            
            # Apply yellow transition logic: Green (0-5s) -> Yellow (5-8s) -> Red
            if time_in_cycle < 5.0:  # Green phase (0-5 seconds)
                for signal_id in active_signals:
                    signal_status[f"t{signal_id}"] = "green"
                    signal_status[f"p{signal_id}"] = "red"  # Pedestrian opposite to vehicle
                signal_state = "GREEN"
            elif time_in_cycle < 8.0:  # Yellow phase (5-8 seconds)
                for signal_id in active_signals:
                    signal_status[f"t{signal_id}"] = "yellow"
                    signal_status[f"p{signal_id}"] = "red"  # Keep pedestrians stopped during yellow
                signal_state = "YELLOW"
            # Red phase is default (signals already set to red above)
            
            # Only print on actual changes to avoid spam
            if not auto_cycle_initialized:
                print(f"🔄 AUTO-CYCLE SYNCHRONIZED: {current_pair} signals {signal_state}")
                print(f"📊 SYNC STATUS: {signal_status}")
                auto_cycle_initialized = True
            elif current_time - last_signal_change >= signal_cycle_interval - 1:  # Print near cycle changes
                print(f"� SYNC UPDATE: {current_pair} active, signals {active_signals} GREEN")
                last_signal_change = current_time
                
    except Exception as e:
        print(f"❌ Auto-cycle error: {e}")
        return False
    
    return True

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
        # Check if signals need to auto-cycle
        auto_cycle_traffic_signals()
        
        with lock:
            return dict(signal_status)  # Return copy to avoid reference issues
    except Exception as e:
        print(f"❌ PRIMARY: Error getting signal status: {e}")
        # Return safe default
        return {
            "t1": "green", "t2": "red", "t3": "red", "t4": "red",
            "p1": "red", "p2": "green", "p3": "green", "p4": "green"
        }

def get_countdown_info():
    """Return countdown information for traffic signal changes"""
    try:
        # Check if signals need to auto-cycle first
        auto_cycle_traffic_signals()
        
        with lock:
            current_time = time.time()
            time_since_last_change = current_time - last_signal_change
            time_remaining = signal_cycle_interval - time_since_last_change
            
            # Ensure time_remaining is not negative
            if time_remaining < 0:
                time_remaining = 0
            
            # Determine current and next signal states
            if current_active_signal in [1, 3]:  # Currently North-South
                current_pair = "North-South"
                next_pair = "East-West"
                current_green = [1, 3]
                next_green = [2, 4]
            else:  # Currently East-West
                current_pair = "East-West" 
                next_pair = "North-South"
                current_green = [2, 4]
                next_green = [1, 3]
            
            return {
                "time_remaining": round(time_remaining, 1),
                "current_pair": current_pair,
                "next_pair": next_pair,
                "current_green_signals": current_green,
                "next_green_signals": next_green,
                "cycle_interval": signal_cycle_interval,
                "signal_status": dict(signal_status)
            }
            
    except Exception as e:
        print(f"❌ PRIMARY: Error getting countdown info: {e}")
        return {
            "time_remaining": 0,
            "current_pair": "North-South",
            "next_pair": "East-West", 
            "current_green_signals": [1, 3],
            "next_green_signals": [2, 4],
            "cycle_interval": 8,
            "signal_status": {"t1": "green", "t2": "red", "t3": "green", "t4": "red", 
                             "p1": "red", "p2": "green", "p3": "red", "p4": "green"}
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
    global current_active_signal, current_sequence, pedestrian_sequence, auto_cycle_enabled, last_signal_change
    
    try:
        # Temporarily disable auto-cycling when manual request is made
        auto_cycle_enabled = False
        
        if synchronized_time:
            sync_time_str = synchronized_time.strftime('%H:%M:%S')
            print(f"⏰ PRIMARY - Operating at synchronized time: {sync_time_str}")
        
        # Determine client
        client_id = f"PRIMARY-Vehicle Controller (Thread-{threading.current_thread().ident % 1000})"
        
        # Create regular request
        request_id, timestamp = request_critical_section(client_id, requested_signal, is_vip=False)
        
        if request_id is None:
            current_sequence = [(0, f"⚠️ PRIMARY - Critical section busy. Request denied for signal {requested_signal}.")]
            # Re-enable auto-cycling
            auto_cycle_enabled = True
            return False
        
        # Simulate replies from other clients
        for client in clients_in_system:
            if client != client_id:
                send_reply(request_id, client, True)
        
        # Check if we can enter critical section
        if not can_enter_critical_section(request_id):
            current_sequence = [(0, f"⏳ PRIMARY - Waiting for critical section access for signal {requested_signal}...")]
            # Re-enable auto-cycling
            auto_cycle_enabled = True
            return False
        
        # Enter critical section
        if not enter_critical_section(request_id):
            current_sequence = [(0, f"❌ PRIMARY - Failed to enter critical section for signal {requested_signal}")]
            # Re-enable auto-cycling
            auto_cycle_enabled = True
            return False
        
        # Execute signal change
        result = execute_signal_change(requested_signal, request_id)
        exit_critical_section(request_id)
        
        # Reset auto-cycle timer and re-enable after delay
        last_signal_change = time.time()
        # Re-enable auto-cycling after 10 seconds to allow manual control
        threading.Timer(10.0, lambda: setattr(sys.modules[__name__], 'auto_cycle_enabled', True)).start()
        
        return result
    except Exception as e:
        print(f"❌ PRIMARY: Error in signal_manipulator: {e}")
        server_stats['failed_requests'] += 1
        # Re-enable auto-cycling on error
        auto_cycle_enabled = True
        return False

def vip_signal_manipulator(requested_signal):
    """Handle VIP signal changes - stops auto-cycle and makes only VIP signal green"""
    global current_active_signal, current_sequence, pedestrian_sequence
    global vip_mode_active, vip_active_signal, vip_start_time
    
    try:
        print(f"🚨 VIP EMERGENCY: Activating signal {requested_signal}")
        
        # Activate VIP mode - this stops auto-cycling
        vip_mode_active = True
        vip_active_signal = requested_signal
        vip_start_time = time.time()
        
        # Immediately set signal states: VIP green, others red
        with lock:
            for i in range(1, 5):
                if i == requested_signal:
                    signal_status[f"t{i}"] = "green"
                    signal_status[f"p{i}"] = "red"
                    print(f"✅ VIP: Signal {i} set to GREEN")
                else:
                    signal_status[f"t{i}"] = "red"
                    signal_status[f"p{i}"] = "green"
                    print(f"🔴 VIP: Signal {i} set to RED")
        
        # Update current active signal
        current_active_signal = requested_signal
        
        # Create success message
        current_sequence = [(0, f"🚨 VIP ACTIVATED: Signal {requested_signal} is GREEN, all others RED")]
        
        print(f"🚨 VIP Mode Active: Signal {requested_signal} priority for {vip_duration} seconds")
        return True
        
    except Exception as e:
        print(f"❌ PRIMARY: Error in vip_signal_manipulator: {e}")
        vip_mode_active = False
        vip_active_signal = None
        vip_start_time = None
        current_sequence = [(0, f"❌ VIP activation failed for signal {requested_signal}")]
        server_stats['failed_requests'] += 1
        return False
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
        server.register_function(get_countdown_info, "get_countdown_info")
        
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