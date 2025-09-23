import xmlrpc.client
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import random
import socket

# UPDATED TO CONNECT TO LOAD BALANCER ON PORT 9000 WITH TIMEOUT HANDLING
def create_server_connection():
    """Create server connection with proper timeout settings"""
    try:
        # Create connection with extended timeout for load testing
        server = xmlrpc.client.ServerProxy(
            "http://127.0.0.1:9000/", 
            allow_none=True,
            transport=xmlrpc.client.Transport(use_datetime=True),
            verbose=False  # Disable verbose logging during load test
        )
        # Set socket timeout to 60 seconds for load testing
        server._ServerProxy__transport.timeout = 60
        return server
    except Exception as e:
        print(f"⚠️ Failed to create server connection: {e}")
        return None

server = create_server_connection()

def register_time_and_sync():
    """Register this client's time and trigger Berkeley synchronization"""
    print("=" * 80)
    print("🔧 MANUAL VIP CONTROLLER - WITH ENHANCED LOAD TESTING")
    print("📊 CONNECTED TO LOAD BALANCER (PORT 9000)")
    print("⚖️ LOAD BALANCER DISTRIBUTES TO PRIMARY (8000) & CLONE (8001)")
    print("🧪 ENHANCED: Signal status load testing with proper error handling")
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
        print("   ┌────────────────────────────────────────┐")
        print("   │              INTERSECTION               │")
        print("   └────────────────────────────────────────┘")
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
    """Execute a single signal status request for load testing with proper error handling"""
    # Create a separate server connection for this thread to avoid conflicts
    thread_server = create_server_connection()
    if not thread_server:
        return f"Request #{request_id}: CONNECTION FAILED"
    
    try:
        print(f"🧪 Load Test Request #{request_id}: Signal Status Query")
        
        # Submit with timeout handling
        start_time = time.time()
        
        # Request signal status (lightweight operation)
        signal_status = thread_server.get_signal_status()
        if not signal_status:
            return f"Request #{request_id}: SIGNAL STATUS FAILED"
        
        # Also get system stats for comprehensive testing
        system_stats = thread_server.get_system_stats()
        
        # Get active signal
        active_signal = thread_server.get_active_signal()
        
        # Get synchronized time
        sync_time = thread_server.get_synchronized_time()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify we got valid responses
        if signal_status and system_stats and active_signal:
            return f"Request #{request_id}: STATUS SUCCESS - Active:{active_signal}, Time:{sync_time} ({duration:.2f}s)"
        else:
            return f"Request #{request_id}: PARTIAL SUCCESS - Some data missing ({duration:.2f}s)"
            
    except xmlrpc.client.Fault as e:
        return f"Request #{request_id}: XML-RPC FAULT - {str(e)}"
    except socket.timeout:
        return f"Request #{request_id}: TIMEOUT - Server response too slow"
    except ConnectionError:
        return f"Request #{request_id}: CONNECTION ERROR - Server unreachable"
    except Exception as e:
        return f"Request #{request_id}: UNEXPECTED ERROR - {str(e)}"

def run_enhanced_load_test():
    """Run enhanced load test with signal status queries instead of VIP requests"""
    print("\n🧪 STARTING ENHANCED SIGNAL STATUS LOAD TEST")
    print("=" * 60)
    print("📊 Enhanced Load Test Parameters:")
    print("   📢 Number of requests: 15 simultaneous signal status queries")
    print("   ⚖️ Server capacity per instance: 10 requests")
    print("   🎯 Expected behavior: 10 -> Primary, 5 -> Clone")
    print("   🔄 Each request uses separate connection")
    print("   ⏱️ Timeout handling: 60 seconds per request")
    print("   🛡️ Error handling: Connection, timeout, XML-RPC faults")
    print("   📊 Test type: Signal status queries (lightweight operations)")
    print("   ✅ Operations: get_signal_status, get_system_stats, get_active_signal")
    print("=" * 60)
    
    # Show initial server stats
    print("\n📊 PRE-TEST SERVER STATUS:")
    display_system_stats()
    
    start_time = time.time()
    
    # Execute 15 requests simultaneously with better concurrency handling
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = []
        
        print(f"\n🚀 LAUNCHING 15 SIMULTANEOUS SIGNAL STATUS QUERIES...")
        
        # Submit all 15 requests at once with staggered timing
        for i in range(1, 16):
            # Small delay between request submissions to avoid overwhelming
            if i > 1:
                time.sleep(0.1)
            
            future = executor.submit(single_load_test_request, i)
            futures.append(future)
        
        # Collect results as they complete with timeout
        results = []
        successful_count = 0
        failed_count = 0
        timeout_count = 0
        
        for i, future in enumerate(futures, 1):
            try:
                # Wait for result with timeout
                result = future.result(timeout=70)  # 70 second timeout per request
                results.append(result)
                
                # Categorize results
                if "SUCCESS" in result:
                    successful_count += 1
                    print(f"✅ {result}")
                elif "TIMEOUT" in result:
                    timeout_count += 1
                    print(f"⏱️ {result}")
                else:
                    failed_count += 1
                    print(f"❌ {result}")
                    
            except Exception as e:
                error_result = f"Request #{i}: EXECUTOR ERROR - {str(e)}"
                results.append(error_result)
                failed_count += 1
                print(f"💥 {error_result}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n📈 ENHANCED LOAD TEST RESULTS:")
    print("=" * 60)
    print(f"⏱️  Total duration: {duration:.2f} seconds")
    print(f"✅ Successful requests: {successful_count}")
    print(f"❌ Failed requests: {failed_count}")
    print(f"⏱️ Timeout requests: {timeout_count}")
    print(f"📊 Total requests: {len(results)}")
    print(f"🎯 Success rate: {(successful_count/len(results)*100):.1f}%")
    if successful_count > 0:
        print(f"📊 Successful requests per second: {successful_count/duration:.2f}")
    
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
    
    # Error analysis
    if failed_count > 0 or timeout_count > 0:
        print(f"\n🔍 ERROR ANALYSIS:")
        print(f"   🚨 Issues detected in {failed_count + timeout_count} requests")
        print(f"   💡 Common causes:")
        print(f"      - Server overload (too many simultaneous connections)")
        print(f"      - XML-RPC transport limitations")
        print(f"      - Network timeout issues")
        print(f"      - Load balancer routing delays")
        print(f"   🛠️ Recommendations:")
        print(f"      - Increase server timeout settings")
        print(f"      - Implement connection pooling")
        print(f"      - Add retry logic for failed requests")
        print(f"      - Monitor server resource usage")
    
    print("=" * 60)

def show_menu():
    """Display the main menu"""
    print("\n" + "=" * 70)
    print("👑 ENHANCED MANUAL VIP CONTROLLER MENU - WITH SIGNAL STATUS LOAD TESTING")
    print("=" * 70)
    print("1. 🚑 Create VIP Request for Route 1")
    print("2. 🚑 Create VIP Request for Route 2") 
    print("3. 🚑 Create VIP Request for Route 3")
    print("4. 🚑 Create VIP Request for Route 4")
    print("5. 📊 View Current Signal Status")
    print("6. 📈 View System Statistics")
    print("7. 🔄 Continuous Status Monitor (press Ctrl+C to stop)")
    print("8. 🧪 RUN LOAD TEST (15 simultaneous signal status queries)")
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
    print("\n👑 ENHANCED VIP CONTROLLER INITIALIZED")
    print("🚨 Ready to dispatch emergency vehicles!")
    print("🔗 Connected via Load Balancer for high availability")
    print("🛡️ Enhanced with robust error handling and timeouts")
    
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
                confirm = input("🧪 Are you sure you want to run the signal status load test? (y/n): ").strip().lower()
                if confirm in ['y', 'yes']:
                    run_enhanced_load_test()
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
            print("🔄 Attempting to reconnect...")
            global server
            server = create_server_connection()
            if not server:
                print("❌ Failed to reconnect. Exiting...")
                break

if __name__ == "__main__":
    if not server:
        print("❌ Failed to create initial server connection. Exiting...")
        exit(1)
        
    if not register_time_and_sync():
        print("❌ Failed to initialize. Exiting...")
        exit(1)
    
    print("\n" + "=" * 80)
    print("👑 ENHANCED VIP EMERGENCY VEHICLE CONTROLLER - LOAD BALANCED VERSION")
    print("🔗 Connected to Load Balancer (Port 9000)")
    print("⚖️ LOAD BALANCING:")
    print("   🟦 Primary Server: http://127.0.0.1:8000/ (Capacity: 10)")
    print("   🟨 Clone Server:   http://127.0.0.1:8001/ (Capacity: 10)")
    print("   📊 Total System Capacity: 20 simultaneous requests")
    print("🚨 ENHANCED VIP CAPABILITIES:")
    print("   ⚡ Manual VIP request generation")
    print("   🎯 Choose specific emergency vehicle routes (1-4)")
    print("   📊 Real-time signal status monitoring")
    print("   🚑 Highest priority processing for VIP requests")
    print("   🔒 Enhanced Ricart-Agrawala with VIP priority")
    print("   🧪 Robust load testing (15 simultaneous requests)")
    print("   🛡️ Enhanced error handling and timeout management")
    print("   🔄 Per-thread connection handling")
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
        print("\n🛑 Enhanced Manual VIP controller stopped.")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("🔄 Check load balancer and server connections...")