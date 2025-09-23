import xmlrpc.client
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import random

# UPDATED TO CONNECT TO LOAD BALANCER ON PORT 9000
server = xmlrpc.client.ServerProxy("http://127.0.0.1:9000/", allow_none=True)
# server = xmlrpc.client.ServerProxy("http://192.168.1.200:9000/", allow_none=True)

def register_time_and_sync():
    """Register this client's time and trigger Berkeley synchronization"""
    print("=" * 80)
    print("🔄 MANUAL VIP CONTROLLER - WITH LOAD TESTING CAPABILITY")
    print("📊 CONNECTED TO LOAD BALANCER (PORT 9000)")
    print("⚖️ LOAD BALANCER DISTRIBUTES TO PRIMARY (8000) & CLONE (8001)")
    print("🧪 NEW FEATURE: Load Test with 15 simultaneous requests")
    print("🚨 VIP VEHICLES GET HIGHEST PRIORITY!")
    print("=" * 80)

    while True:
        controller_time = input("🕐 Enter Manual Controller time (HH:MM:SS): ")
        try:
            hour, minute, second = map(int, controller_time.split(':'))
            if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                break
            else:
                print("❌ Invalid time values. Please use valid HH:MM:SS format.")
        except:
            print("❌ Invalid time format. Please use HH:MM:SS")
    
    print("🔗 Connecting to Load Balancer...")
    
    try:
        success = server.register_client_time("Manual VIP Controller", controller_time)
        if success:
            print("✅ Manual VIP Controller time registered successfully!")
        else:
            print("❌ Failed to register time")
            return False
        
        print("⏳ Waiting for Berkeley Algorithm synchronization...")
        time.sleep(2)

        sync_time = server.get_synchronized_time()
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
    """Display current signal status array in a nice format"""
    try:
        status = server.get_signal_status()
        print("\n📊 CURRENT SIGNAL STATUS:")
        print("   ┌─────────────────────────────────────────┐")
        print("   │              INTERSECTION               │")
        print("   └─────────────────────────────────────────┘")
        print(f"   Traffic Signals:     T1:{status['t1'].upper():>5} | T2:{status['t2'].upper():>5} | T3:{status['t3'].upper():>5} | T4:{status['t4'].upper():>5}")
        print(f"   Pedestrian Crossings: P1:{status['p1'].upper():>5} | P2:{status['p2'].upper():>5} | P3:{status['p3'].upper():>5} | P4:{status['p4'].upper():>5}")
        
        # Show which signal is currently active
        active_signal = server.get_active_signal()
        print(f"   🟢 Currently GREEN: Traffic Signal {active_signal}")
        
        return status
    except Exception as e:
        print(f"❌ Failed to get signal status: {e}")
        return None

def display_system_stats():
    """Display system statistics including load balancer stats"""
    try:
        stats = server.get_system_stats()
        sync_time = server.get_synchronized_time()
        
        print("\n📈 SYSTEM STATISTICS:")
        if sync_time:
            print(f"   ⏰ Synchronized time: {sync_time}")
        
        print(f"   📊 Total requests processed: {stats.get('total_requests_processed', 0)}")
        print(f"   👑 VIP requests processed: {stats.get('vip_requests_processed', 0)}")
        print(f"   ⏳ Pending requests: {stats.get('pending_requests', 0)}")
        print(f"   🚨 VIP pending: {stats.get('vip_pending_requests', 0)}")
        
        # Load balancer specific stats
        if 'total_requests' in stats:
            print(f"\n🔄 LOAD BALANCER STATISTICS:")
            print(f"   📡 Total requests routed: {stats.get('total_requests', 0)}")
            print(f"   ⚖️ Load balanced requests: {stats.get('load_balanced_requests', 0)}")
            print(f"   🟦 Primary server load: {stats.get('server_0_load', 'N/A')}")
            print(f"   🟨 Clone server load: {stats.get('server_1_load', 'N/A')}")
        
        if stats.get('in_critical_section'):
            print(f"   🔒 Critical section: {stats['in_critical_section']}")
        else:
            print("   🔓 Critical section: Available")
        
    except Exception as e:
        print(f"❌ Failed to get system stats: {e}")

def create_vip_request(route_number):
    """Create a VIP request for the specified route"""
    try:
        # Create timestamp for VIP request
        current_time = int(time.time())
        base_time = 1700000000  # Base timestamp to keep numbers smaller
        relative_timestamp = current_time - base_time
        
        vip_data = [(route_number, relative_timestamp)]
        
        print(f"\n🚨 CREATING VIP EMERGENCY REQUEST:")
        print(f"   🚑 Emergency Vehicle Route: {route_number}")
        print(f"   ⏰ Request Timestamp: {relative_timestamp}")
        print(f"   🚨 Priority Level: HIGHEST")
        print(f"   🔗 Routing through Load Balancer")
        
        # Submit VIP request to server via load balancer
        success = server.submit_vip_requests(vip_data)
        
        if success:
            print("   ✅ VIP request submitted successfully!")
            
            # Process the VIP request
            print("\n👑 PROCESSING VIP REQUEST:")
            vip_success = server.vip_signal_manipulator(route_number)
            
            if vip_success:
                print("   🚨 VIP signal manipulation initiated!")
                
                # Collect and display VIP messages
                message_count = 0
                print(f"\n🚑 VIP SIGNAL CHANGE SEQUENCE FOR ROUTE {route_number}:")
                
                while True:
                    msg = server.get_next_message()
                    if msg is None:
                        break
                    message_count += 1
                    print(f"   👑 VIP: {msg}")
                
                if message_count == 0:
                    print(f"   ℹ️ VIP: Route {route_number} was already active or no change needed")
                else:
                    print(f"   ✅ VIP signal change to route {route_number} completed!")
                
                # Show updated status
                display_signal_status()
                
            else:
                print("   ❌ VIP signal manipulation failed!")
                
        else:
            print("   ❌ Failed to submit VIP request!")
            
    except Exception as e:
        print(f"❌ Error creating VIP request: {e}")

def single_load_test_request(request_id):
    """Execute a single request for load testing"""
    try:
        route = random.randint(1, 4)  # Random route 1-4
        
        print(f"🧪 Load Test Request #{request_id}: Route {route}")
        
        # Create VIP request
        current_time = int(time.time())
        base_time = 1700000000
        relative_timestamp = current_time - base_time + request_id  # Unique timestamp
        
        vip_data = [(route, relative_timestamp)]
        
        # Submit and process
        success = server.submit_vip_requests(vip_data)
        if success:
            result = server.vip_signal_manipulator(route)
            return f"Request #{request_id} -> Route {route}: {'SUCCESS' if result else 'FAILED'}"
        else:
            return f"Request #{request_id} -> Route {route}: SUBMIT FAILED"
            
    except Exception as e:
        return f"Request #{request_id}: ERROR - {str(e)}"

def run_load_test():
    """Run load test with 15 simultaneous requests to test server capacity"""
    print("\n🧪 STARTING LOAD TEST")
    print("=" * 60)
    print("📊 Load Test Parameters:")
    print("   🔢 Number of requests: 15")
    print("   ⚖️ Server capacity per instance: 10 requests")
    print("   🎯 Expected behavior: 10 -> Primary, 5 -> Clone")
    print("   🔄 All requests submitted simultaneously")
    print("=" * 60)
    
    # Show initial server stats
    print("\n📊 PRE-TEST SERVER STATUS:")
    display_system_stats()
    
    start_time = time.time()
    
    # Execute 15 requests simultaneously using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = []
        
        print(f"\n🚀 LAUNCHING 15 SIMULTANEOUS REQUESTS...")
        
        # Submit all 15 requests at once
        for i in range(1, 16):
            future = executor.submit(single_load_test_request, i)
            futures.append(future)
        
        # Collect results as they complete
        results = []
        for future in futures:
            try:
                result = future.result(timeout=30)  # 30 second timeout
                results.append(result)
                print(f"✅ {result}")
            except Exception as e:
                results.append(f"Request failed: {e}")
                print(f"❌ Request failed: {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n📈 LOAD TEST RESULTS:")
    print("=" * 60)
    print(f"⏱️  Total duration: {duration:.2f} seconds")
    print(f"✅ Successful requests: {sum(1 for r in results if 'SUCCESS' in r)}")
    print(f"❌ Failed requests: {sum(1 for r in results if 'FAILED' in r or 'ERROR' in r)}")
    print(f"📊 Requests per second: {15/duration:.2f}")
    
    # Show final server stats
    print(f"\n📊 POST-TEST SERVER STATUS:")
    display_system_stats()
    
    print("=" * 60)
    print("🔄 LOAD BALANCING ANALYSIS:")
    try:
        stats = server.get_system_stats()
        if stats:
            total_routed = stats.get('total_requests', 0)
            load_balanced = stats.get('load_balanced_requests', 0)
            
            print(f"   📡 Total requests routed by load balancer: {total_routed}")
            print(f"   ⚖️ Requests sent to clone server: {load_balanced}")
            print(f"   🟦 Requests handled by primary server: {total_routed - load_balanced}")
            
            if load_balanced > 0:
                print("   ✅ LOAD BALANCING SUCCESSFUL!")
                print("   🎯 Clone server activated when primary reached capacity")
            else:
                print("   ℹ️ All requests handled by primary server")
                print("   💡 Primary server had sufficient capacity")
        
    except Exception as e:
        print(f"   ❌ Could not retrieve load balancing stats: {e}")
    
    print("=" * 60)

def show_menu():
    """Display the main menu"""
    print("\n" + "=" * 70)
    print("👑 MANUAL VIP CONTROLLER MENU - WITH LOAD TESTING")
    print("=" * 70)
    print("1. 🚑 Create VIP Request for Route 1")
    print("2. 🚑 Create VIP Request for Route 2") 
    print("3. 🚑 Create VIP Request for Route 3")
    print("4. 🚑 Create VIP Request for Route 4")
    print("5. 📊 View Current Signal Status")
    print("6. 📈 View System Statistics")
    print("7. 🔄 Continuous Status Monitor (press Ctrl+C to stop)")
    print("8. 🧪 RUN LOAD TEST (15 simultaneous requests)")
    print("9. ❌ Exit")
    print("=" * 70)

def continuous_monitor():
    """Continuously display signal status updates"""
    print("\n🔄 STARTING CONTINUOUS SIGNAL STATUS MONITOR")
    print("   Press Ctrl+C to return to main menu")
    print("   Updates every 2 seconds")
    print("   🔗 Monitoring through Load Balancer")
    
    try:
        while True:
            display_signal_status()
            display_system_stats()
            time.sleep(2)
            print("\n" + "─" * 50)  # Separator line
            
    except KeyboardInterrupt:
        print("\n🛑 Continuous monitor stopped.")

def main_controller():
    """Main VIP controller interface"""
    print("\n👑 VIP CONTROLLER INITIALIZED")
    print("🚨 Ready to dispatch emergency vehicles!")
    print("🔗 Connected via Load Balancer for high availability")
    
    while True:
        try:
            show_menu()
            choice = input("\n🎯 Select option (1-9): ").strip()
            
            if choice == '1':
                create_vip_request(1)
            elif choice == '2':
                create_vip_request(2)
            elif choice == '3':
                create_vip_request(3)
            elif choice == '4':
                create_vip_request(4)
            elif choice == '5':
                display_signal_status()
            elif choice == '6':
                display_system_stats()
            elif choice == '7':
                continuous_monitor()
            elif choice == '8':
                confirm = input("🧪 Are you sure you want to run the load test? (y/n): ").strip().lower()
                if confirm in ['y', 'yes']:
                    run_load_test()
                else:
                    print("🚫 Load test cancelled.")
            elif choice == '9':
                print("👑 VIP Controller shutting down...")
                break
            else:
                print("❌ Invalid choice. Please select 1-9.")
                
        except KeyboardInterrupt:
            print("\n🛑 VIP Controller interrupted.")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    if not register_time_and_sync():
        print("❌ Failed to initialize. Exiting...")
        exit(1)
    
    print("\n" + "=" * 80)
    print("👑 VIP EMERGENCY VEHICLE CONTROLLER - LOAD BALANCED VERSION")
    print("🔗 Connected to Load Balancer (Port 9000)")
    print("⚖️ LOAD BALANCING:")
    print("   🟦 Primary Server: http://127.0.0.1:8000/ (Capacity: 10)")
    print("   🟨 Clone Server:   http://127.0.0.1:8001/ (Capacity: 10)")
    print("   📊 Total System Capacity: 20 simultaneous requests")
    print("🚨 VIP CAPABILITIES:")
    print("   ⚡ Manual VIP request generation")
    print("   🎯 Choose specific emergency vehicle routes (1-4)")
    print("   📊 Real-time signal status monitoring")
    print("   🚑 Highest priority processing for VIP requests")
    print("   🔒 Enhanced Ricart-Agrawala with VIP priority")
    print("   🧪 Load testing capability (15 simultaneous requests)")
    print("📊 SIGNAL STATUS ARRAY: Synchronized across all servers")
    print("🎲 VIP Generation: Manual control (no random generation)")
    print("=" * 80)
    
    # Display initial status
    display_signal_status()
    display_system_stats()
    
    try:
        # Run the VIP controller
        main_controller()
    except KeyboardInterrupt:
        print("\n🛑 Manual VIP controller stopped.")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("🔄 Check load balancer and server connections...")