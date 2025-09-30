import xmlrpc.client
import random
import time
import threading
from queue import Queue

# UPDATED TO CONNECT TO LOAD BALANCER ON PORT 9000
# server = xmlrpc.client.ServerProxy("http://192.168.1.200:9000/", allow_none=True)
server = xmlrpc.client.ServerProxy("http://127.0.0.1:9000/", allow_none=True)

def register_time_and_sync():
    """Register this client's time and trigger Berkeley synchronization"""
    print("=" * 80)
    print("🚗 FOUR-WAY VEHICLE CONTROLLER - LOAD BALANCED VERSION 🚙")
    print("📊 CONNECTED TO LOAD BALANCER (PORT 9000)")
    print("⚖️ LOAD BALANCER DISTRIBUTES TO PRIMARY (8000) & CLONE (8001)")
    print("🔥 GENERATES REGULAR SIGNAL REQUESTS (NO VIP)")
    print("⚡ REQUESTING ACCESS TO CHANGE SIGNALS (ONLY 1 GREEN AT A TIME)")
    print("👑 VIP requests now handled by tm.py")
    print("📊 Shows current signal status array")
    print("=" * 80)

    while True:
        traffic_time = input("🕐 Enter Traffic Signal time (HH:MM:SS): ")
        try:
            hour, minute, second = map(int, traffic_time.split(':'))
            if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                break
            else:
                print("❌ Invalid time values. Please use valid HH:MM:SS format.")
        except:
            print("❌ Invalid time format. Please use HH:MM:SS")
    
    print("🔗 Connecting to Load Balancer...")
    
    try:
        success = server.register_client_time("Traffic Signal", traffic_time)
        if success:
            print("✅ Traffic Signal time registered successfully!")
        else:
            print("❌ Failed to register time")
            return False
        
        print("⏳ Waiting for all clients to connect...")
        time.sleep(3)

        sync_time = server.berkeley_synchronization()
        if sync_time:
            print(f"\n🎯 FINAL SYNCHRONIZED TIME: {sync_time}")
            print("✅ All traffic systems are now synchronized!")
        else:
            print("⏳ Synchronization pending - waiting for all clients...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during time synchronization: {e}")
        return False

def display_signal_status():
    """Display current signal status array"""
    try:
        status = server.get_signal_status()
        print("📊 CURRENT SIGNAL STATUS:")
        print(f"   Traffic:     T1:{status['t1']} | T2:{status['t2']} | T3:{status['t3']} | T4:{status['t4']}")
        print(f"   Pedestrian:  P1:{status['p1']} | P2:{status['p2']} | P3:{status['p3']} | P4:{status['p4']}")
    except Exception as e:
        print(f"❌ Failed to get signal status: {e}")

def generate_signal_requests():
    """Generate 1-2 random signal requests (1, 2, 3, or 4)"""
    all_signals = [1, 2, 3, 4]
    num_requests = random.choice([1, 2])  # Randomly choose to make 1 or 2 requests
    
    if num_requests == 1:
        return [random.choice(all_signals)]
    else:
        # For 2 requests, ensure they're different signals
        selected = random.sample(all_signals, 2)
        return selected

def process_single_signal_request(signal_id, worker_id, results_queue):
    """Process a single signal request and put results in queue"""
    try:
        print(f"🔥 Worker {worker_id}: Requesting regular signal {signal_id} via Load Balancer")
        success = server.signal_manipulator(signal_id)
        
        if not success:
            print(f"❌ Worker {worker_id}: Signal {signal_id} request was denied or failed")
            results_queue.put((worker_id, signal_id, False, []))
            return

        # Collect all messages for this request
        messages = []
        message_count = 0
        
        print(f"\n🚦 Worker {worker_id} - SIGNAL {signal_id} CHANGE SEQUENCE:")
        
        while True:
            msg = server.get_next_message()
            if msg is None:
                break
            message_count += 1
            messages.append(msg)
            print(f"🚗 Worker {worker_id}: {msg}")
        
        if message_count == 0:
            print(f"ℹ️ Worker {worker_id}: No signal changes were needed for signal {signal_id}.")
            messages.append(f"ℹ️ Signal {signal_id} was already active or no change needed")
        else:
            print(f"✅ Worker {worker_id}: Signal change to {signal_id} completed!")
            
        results_queue.put((worker_id, signal_id, True, messages))
            
    except Exception as e:
        print(f"❌ Worker {worker_id} error communicating with load balancer: {e}")
        results_queue.put((worker_id, signal_id, False, [str(e)]))

def t_signal():
    """Control four-way traffic signals with regular requests only"""
    try:
        # Generate 1-2 random REGULAR signal requests
        requested_signals = generate_signal_requests()
        num_regular_requests = len(requested_signals)
        
        print(f"\n📋 REGULAR SIGNAL REQUESTS:")
        print(f"   🔥 Regular signals requested: {requested_signals} ({num_regular_requests} requests)")
        print(f"   ⚡ RULE: Only ONE signal can be GREEN at a time!")
        print(f"   👑 VIP requests handled separately by tm.py")
        print(f"   📡 Routing through Load Balancer")
        
        # Process all requests sequentially
        results_queue = Queue()
        
        print(f"\n⏱️ PROCESSING ALL REQUESTS VIA LOAD BALANCER:")
        print(f"   📋 Total requests: {len(requested_signals)} regular")
        
        # Process requests sequentially to avoid XML-RPC conflicts
        for i, signal_id in enumerate(requested_signals, 1):
            print(f"\n📋 PROCESSING REGULAR REQUEST #{i} VIA LOAD BALANCER:")
            print(f"   🎯 Regular Signal: {signal_id}")
            print(f"   🔄 Normal priority processing")
            
            # Process one request at a time
            worker_thread = threading.Thread(
                target=process_single_signal_request, 
                args=(signal_id, f"T{i}", results_queue),
                name=f"SignalWorker-{signal_id}-REG"
            )
            worker_thread.start()
            worker_thread.join()  # Wait for this request to complete
            # Small delay between requests
            time.sleep(0.5)
        
        # Collect and display results
        print(f"\n📊 PROCESSING RESULTS:")
        regular_processed = 0
        
        while not results_queue.empty():
            worker_id, signal_id, success, messages = results_queue.get()
            
            if success:
                regular_processed += 1
                print(f"✅ {worker_id}: Regular signal {signal_id} processed successfully via Load Balancer")
            else:
                print(f"❌ {worker_id}: Regular signal {signal_id} failed")
        
        print(f"\n✅ ALL REQUESTS PROCESSED VIA LOAD BALANCER!")
        print(f"   📋 Regular requests completed: {regular_processed}")
        print("🔒 Mutual exclusion maintained - all requests processed atomically")
        print("⚖️ Load balancer distributed requests between primary and clone servers")
            
    except Exception as e:
        print("❌ Error communicating with load balancer:", e)

def display_status():
    """Display current synchronized time, active signal, and system status"""
    try:
        sync_time = server.get_synchronized_time()
        active_signal = server.get_active_signal()
        stats = server.get_system_stats()
        
        if sync_time:
            print(f"⏰ Current synchronized time: {sync_time}")
        if active_signal:
            print(f"🟢 Currently GREEN signal: {active_signal}")
            red_signals = [sig for sig in [1, 2, 3, 4] if sig != active_signal]
            print(f"🔴 Currently RED signals: {red_signals}")
        
        # Display system statistics including load balancer info
        if stats:
            print(f"📊 System Status:")
            print(f"   Total requests processed: {stats.get('total_requests_processed', 0)}")
            print(f"   VIP requests processed: {stats.get('vip_requests_processed', 0)}")
            print(f"   Pending requests: {stats.get('pending_requests', 0)}")
            
            # Load balancer stats
            if 'total_requests' in stats:
                print(f"\n📡 LOAD BALANCER STATUS:")
                print(f"   📊 Total requests routed: {stats.get('total_requests', 0)}")
                print(f"   ⚖️ Load balanced requests: {stats.get('load_balanced_requests', 0)}")
        
        # Display signal status array
        display_signal_status()
                
    except Exception as e:
        print(f"❌ Status check failed: {e}")

if __name__ == "__main__":
    if not register_time_and_sync():
        print("❌ Failed to initialize. Exiting...")
        exit(1)
    
    print("\n" + "=" * 80)
    print("🚦 FOUR-WAY INTERSECTION - LOAD BALANCED REGULAR SIGNAL CONTROLLER")
    print("📡 CONNECTED TO LOAD BALANCER (PORT 9000)")
    print("⚖️ LOAD BALANCING:")
    print("   🟦 Primary Server: http://127.0.0.1:8000/ (Capacity: 10)")
    print("   🟨 Clone Server:   http://127.0.0.1:8001/ (Capacity: 10)")
    print("   📊 Total System Capacity: 20 simultaneous requests")
    print("🔒 Using Ricart-Agrawala Algorithm for Critical Section Access")
    print("📋 REGULAR REQUESTS ONLY: No VIP generation in this client")
    print("⚡ RULE: Only ONE signal can be GREEN at a time!")
    print("🎲 Regular signals: Always generated (1-2 requests)")
    print("👑 VIP vehicles: Handled by tm.py")
    print("📊 Signal status array: Real-time updates from server")
    print("🔥 Processes requests sequentially to avoid conflicts")
    print("=" * 80)

    # Display initial status
    display_status()

    while True:
        try:
            t_signal()
            print(f"\n⏳ Waiting before next cycle (regular requests only)...\n")
            time.sleep(4)
        except KeyboardInterrupt:
            print("\nπŸ›' Four-way vehicle signal controller stopped manually.")
            break
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("🔄 Attempting to reconnect to load balancer...")
            time.sleep(5)