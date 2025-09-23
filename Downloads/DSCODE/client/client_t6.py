import xmlrpc.client
import random
import time
import threading
from queue import Queue

server = xmlrpc.client.ServerProxy("http://192.168.1.100:8000/", allow_none=True)

def register_time_and_sync():
    """Register this client's time and trigger Berkeley synchronization"""
    print("=" * 80)
    print("🚗 FOUR-WAY VEHICLE CONTROLLER - VIP PRIORITY RICART-AGRAWALA 🚙")
    print("👑 GENERATES BOTH: Regular signals + VIP vehicles separately!")
    print("⚡ REQUESTING ACCESS TO CHANGE SIGNALS (ONLY 1 GREEN AT A TIME)")
    print("🎲 VIP GENERATION: 1/3 chance, separate from regular signals")
    print("🚨 VIPs get HIGHER PRIORITY in processing queue")
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
    
    print("🔗 Connecting to VIP-Priority Signal Manipulator Server...")
    
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

def generate_vip_vehicles():
    """Generate VIP vehicles with 1/3 probability - SEPARATE from regular signals"""
    if random.random() > 1/3:  # 1/3 chance of VIP generation
        return []
    
    num_vips = random.randint(1, 2)  # 1-2 VIPs
    vip_vehicles = []
    
    for i in range(num_vips):
        route = random.randint(1, 4)  # Routes 1-4
        # FIX: Use a smaller timestamp that fits XML-RPC limits
        # Instead of milliseconds since epoch, use seconds since a recent base time
        base_time = 1700000000  # A recent timestamp (Nov 2023)
        current_time = int(time.time())
        relative_timestamp = current_time - base_time  # Much smaller number
        
        vip_vehicles.append((route, relative_timestamp))
    
    return vip_vehicles

def process_single_signal_request(signal_id, worker_id, results_queue, is_vip=False):
    """Process a single signal request and put results in queue"""
    try:
        if is_vip:
            print(f"👑 VIP Worker {worker_id}: Processing VIP route {signal_id}")
            success = server.vip_signal_manipulator(signal_id)
        else:
            print(f"🔥 Worker {worker_id}: Requesting regular signal {signal_id}")
            success = server.signal_manipulator(signal_id)
        
        if not success:
            print(f"❌ Worker {worker_id}: Signal {signal_id} request was denied or failed")
            results_queue.put((worker_id, signal_id, False, [], is_vip))
            return

        # Collect all messages for this request
        messages = []
        message_count = 0
        
        if is_vip:
            print(f"\n👑 VIP Worker {worker_id} - SIGNAL {signal_id} CHANGE SEQUENCE:")
        else:
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
            
        results_queue.put((worker_id, signal_id, True, messages, is_vip))
            
    except Exception as e:
        print(f"❌ Worker {worker_id} error communicating with server: {e}")
        results_queue.put((worker_id, signal_id, False, [str(e)], is_vip))

def t_signal():
    """Control four-way traffic signals with both regular and VIP requests"""
    try:
        # Get current active signal
        current_active = server.get_active_signal()
        print(f"\n🔍 Current active signal: {current_active} (GREEN)")
        
        # All other signals are RED
        all_signals = [1, 2, 3, 4]
        red_signals = [sig for sig in all_signals if sig != current_active]
        print(f"🔴 Signals currently RED: {red_signals}")
        
        # Generate 1-2 random REGULAR signal requests (ALWAYS GENERATED)
        requested_signals = generate_signal_requests()
        num_regular_requests = len(requested_signals)
        
        # Generate VIP vehicles (1/3 CHANCE, SEPARATE)
        vip_vehicles = generate_vip_vehicles()
        num_vip_requests = len(vip_vehicles)
        
        print(f"\n🔍 TWO-INPUT SYSTEM:")
        print(f"   📝 REGULAR SIGNALS (always generated): {requested_signals} ({num_regular_requests} requests)")
        if vip_vehicles:
            print(f"   👑 VIP VEHICLES (1/3 chance): {[vip[0] for vip in vip_vehicles]} ({num_vip_requests} VIPs)")
            print(f"   🚨 VIPs will be processed FIRST due to higher priority!")
        else:
            print(f"   👑 VIP VEHICLES: None generated this cycle")
        
        print(f"   ⚡ RULE: Only ONE signal can be GREEN at a time!")
        print(f"   🎯 PROCESSING ORDER: VIPs first, then regular requests")
        
        # Submit VIPs to server first if any exist
        if vip_vehicles:
            print(f"\n🚨 SUBMITTING VIP REQUESTS:")
            server.submit_vip_requests(vip_vehicles)
        
        # Process all requests (VIPs get priority automatically on server side)
        results_queue = Queue()
        all_requests = []
        
        # Add VIP requests first (they'll be processed with higher priority)
        for i, (vip_route, vip_timestamp) in enumerate(vip_vehicles, 1):
            all_requests.append((vip_route, f"VIP{i}", True))
        
        # Add regular requests
        for i, signal_id in enumerate(requested_signals, 1):
            all_requests.append((signal_id, f"T{i}", False))
        
        print(f"\n⏱️ PROCESSING ALL REQUESTS:")
        print(f"   📋 Total requests: {len(all_requests)} ({num_vip_requests} VIP + {num_regular_requests} regular)")
        
        # Process requests sequentially to avoid XML-RPC conflicts
        for signal_id, worker_id, is_vip in all_requests:
            if is_vip:
                print(f"\n👑 PROCESSING VIP REQUEST:")
                print(f"   🎯 VIP Route: {signal_id}")
                print(f"   ⚡ HIGH PRIORITY - will be processed first")
            else:
                print(f"\n📝 PROCESSING REGULAR REQUEST:")
                print(f"   🎯 Regular Signal: {signal_id}")
                print(f"   🔄 Normal priority - processed after VIPs")
            
            # Process one request at a time
            worker_thread = threading.Thread(
                target=process_single_signal_request, 
                args=(signal_id, worker_id, results_queue, is_vip),
                name=f"SignalWorker-{signal_id}-{'VIP' if is_vip else 'REG'}"
            )
            worker_thread.start()
            worker_thread.join()  # Wait for this request to complete
            
            # Small delay between requests
            time.sleep(0.5)
        
        # Collect and display results
        print(f"\n📊 PROCESSING RESULTS:")
        vip_processed = 0
        regular_processed = 0
        
        while not results_queue.empty():
            worker_id, signal_id, success, messages, is_vip = results_queue.get()
            
            if success:
                if is_vip:
                    vip_processed += 1
                    print(f"👑 {worker_id}: VIP route {signal_id} processed successfully")
                else:
                    regular_processed += 1
                    print(f"✅ {worker_id}: Regular signal {signal_id} processed successfully")
            else:
                if is_vip:
                    print(f"❌ {worker_id}: VIP route {signal_id} failed")
                else:
                    print(f"❌ {worker_id}: Regular signal {signal_id} failed")
        
        print(f"\n✅ ALL REQUESTS PROCESSED!")
        print(f"   👑 VIP requests completed: {vip_processed}")
        print(f"   📝 Regular requests completed: {regular_processed}")
        
        if vip_vehicles:
            print("🚨 VIP PRIORITY SYSTEM ACTIVATED:")
            print("   ⚡ VIPs were processed with higher priority")
            print("   🎯 VIPs processed first, then regular requests")
        
        print("🔒 Mutual exclusion maintained - all requests processed atomically")
        
        # Show final state
        final_active = server.get_active_signal()
        if final_active != current_active:
            print(f"🔄 Signal state changed: {current_active} → {final_active}")
        else:
            print(f"🔄 Signal state unchanged: {current_active} (no valid changes needed)")
            
    except Exception as e:
        print("❌ Error communicating with server:", e)

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
        
        # Display system statistics
        if stats:
            print(f"📊 System Status:")
            print(f"   Total requests processed: {stats.get('total_requests_processed', 0)}")
            print(f"   VIP requests processed: {stats.get('vip_requests_processed', 0)}")
            print(f"   Pending requests: {stats.get('pending_requests', 0)}")
                
    except Exception as e:
        print(f"❌ Status check failed: {e}")

if __name__ == "__main__":
    if not register_time_and_sync():
        print("❌ Failed to initialize. Exiting...")
        exit(1)
    
    print("\n" + "=" * 80)
    print("🚦 FOUR-WAY INTERSECTION - VIP PRIORITY CONTROLLER")
    print("🔒 Using Ricart-Agrawala Algorithm for Critical Section Access")
    print("👑 TWO-INPUT SYSTEM: Regular signals + VIP vehicles (separate generation)")
    print("⚡ RULE: Only ONE signal can be GREEN at a time!")
    print("🎲 Regular signals: Always generated (1-2 requests)")
    print("🚨 VIP vehicles: 1/3 chance (1-2 VIPs) - GET HIGHER PRIORITY!")
    print("📝 Same signal change messages for both VIP and regular")
    print("🔥 Processes requests sequentially to avoid conflicts")
    print("🛡️ VIP priority handled by server-side Enhanced Ricart-Agrawala!")
    print("=" * 80)

    # Display initial status
    display_status()

    while True:
        try:
            t_signal()
            print(f"\n⏳ Waiting before next cycle (VIP chance: 1/3, regular: always)...\n")
            time.sleep(4)
        except KeyboardInterrupt:
            print("\n🛑 VIP-priority four-way vehicle signal controller stopped manually.")
            break
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("🔄 Attempting to reconnect...")
            time.sleep(5)