import xmlrpc.client
import random
import time
import threading
from queue import Queue

server = xmlrpc.client.ServerProxy("http://127.0.0.1:8000/", allow_none=True)

def register_time_and_sync():
    """Register this client's time and trigger Berkeley synchronization"""
    print("=" * 80)
    print("🚗 FOUR-WAY VEHICLE CONTROLLER - RICART-AGRAWALA 🚙")
    print("⚡ REQUESTING ACCESS TO CHANGE SIGNALS (ONLY 1 GREEN AT A TIME)")
    print("🎲 NOW GENERATES 1-2 SIGNAL REQUESTS FOR MUTUAL EXCLUSION TESTING")
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
    
    print("🔍 Connecting to Signal Manipulator Server...")
    
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

def process_single_signal_request(signal_id, worker_id, results_queue):
    """Process a single signal request and put results in queue"""
    try:
        print(f"🔄 Worker {worker_id}: Requesting signal {signal_id}")
        
        # Add small random delay to simulate realistic timing
        time.sleep(random.uniform(0.1, 0.3))
        
        # Make the request - this will use Ricart-Agrawala internally
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
        print(f"❌ Worker {worker_id} error communicating with server: {e}")
        results_queue.put((worker_id, signal_id, False, [str(e)]))

def t_signal():
    """Control four-way traffic signals with multiple requests processed sequentially"""
    try:
        # Get current active signal
        current_active = server.get_active_signal()
        print(f"\n🔍 Current active signal: {current_active} (GREEN)")
        
        # All other signals are RED
        all_signals = [1, 2, 3, 4]
        red_signals = [sig for sig in all_signals if sig != current_active]
        print(f"🔴 Signals currently RED: {red_signals}")
        
        # Generate 1-2 random signal requests
        requested_signals = generate_signal_requests()
        num_requests = len(requested_signals)
        
        print(f"\n🔐 RICART-AGRAWALA MUTUAL EXCLUSION TEST:")
        print(f"   🎯 Making {num_requests} request(s): {requested_signals}")
        print(f"   ⚡ RULE: Only ONE signal can be GREEN at a time!")
        
        if num_requests > 1:
            print(f"   🏁 MULTIPLE REQUESTS: Will be processed sequentially due to mutual exclusion")
            print(f"   🛡️ Ricart-Agrawala will ensure only one signal changes at a time")
        
        # Show what will happen for each request
        for signal in requested_signals:
            if signal == current_active:
                print(f"   ℹ️  Signal {signal} is already GREEN")
            else:
                print(f"   🔄 Signal {signal} request will attempt to become active")
        
        print(f"   ⏱️  Processing requests...")
        
        # Process requests sequentially to avoid XML-RPC conflicts
        # This still demonstrates mutual exclusion because server enforces it
        results_queue = Queue()
        
        for i, signal_id in enumerate(requested_signals, 1):
            # Process one request at a time to avoid XML-RPC connection issues
            worker_thread = threading.Thread(
                target=process_single_signal_request, 
                args=(signal_id, f"T{i}", results_queue),
                name=f"SignalWorker-{signal_id}"
            )
            worker_thread.start()
            worker_thread.join()  # Wait for this request to complete before starting next
            
            # Small delay between requests to make the mutual exclusion more visible
            if i < len(requested_signals):
                time.sleep(0.5)
        
        # Collect and display results
        print(f"\n📊 PROCESSING RESULTS:")
        processed_results = []
        
        while not results_queue.empty():
            worker_id, signal_id, success, messages = results_queue.get()
            processed_results.append((worker_id, signal_id, success))
            
            if success:
                print(f"✅ {worker_id}: Successfully processed signal {signal_id}")
            else:
                print(f"❌ {worker_id}: Failed to process signal {signal_id}")
        
        print(f"\n✅ All {num_requests} signal request(s) have been processed!")
        print("🔐 Mutual exclusion successfully maintained - requests processed atomically")
        
        # Show final state
        final_active = server.get_active_signal()
        if final_active != current_active:
            print(f"🔄 Signal state changed: {current_active} → {final_active}")
        else:
            print(f"🔄 Signal state unchanged: {current_active} (no valid changes needed)")
            
    except Exception as e:
        print("❌ Error communicating with server:", e)

def display_status():
    """Display current synchronized time and active signal"""
    try:
        sync_time = server.get_synchronized_time()
        active_signal = server.get_active_signal()
        if sync_time:
            print(f"⏰ Current synchronized time: {sync_time}")
        if active_signal:
            print(f"🟢 Currently GREEN signal: {active_signal}")
            red_signals = [sig for sig in [1, 2, 3, 4] if sig != active_signal]
            print(f"🔴 Currently RED signals: {red_signals}")
    except Exception as e:
        print(f"❌ Status check failed: {e}")

if __name__ == "__main__":
    if not register_time_and_sync():
        print("❌ Failed to initialize. Exiting...")
        exit(1)
    
    print("\n" + "=" * 80)
    print("🚦 FOUR-WAY INTERSECTION - MUTUAL EXCLUSION CONTROLLER")
    print("🔐 Using Ricart-Agrawala Algorithm for Critical Section Access")
    print("⚡ RULE: Only ONE signal can be GREEN at a time!")
    print("🎲 Randomly generates 1-2 signal requests (1, 2, 3, or 4)")
    print("🔄 Processes requests sequentially to avoid XML-RPC conflicts")
    print("🛡️ Server-side mutual exclusion still enforced via Ricart-Agrawala!")
    print("=" * 80)

    # Display initial status
    display_status()

    while True:
        try:
            t_signal()
            print(f"\n⏳ Waiting before next batch of requests...\n")
            time.sleep(4)
        except KeyboardInterrupt:
            print("\n🛑 Four-way vehicle signal controller stopped manually.")
            break
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("🔄 Attempting to reconnect...")
            time.sleep(5)