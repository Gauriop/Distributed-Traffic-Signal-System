import xmlrpc.client
import time
import threading

server = xmlrpc.client.ServerProxy("http://127.0.0.1:8000/", allow_none=True)

def register_time_and_sync():
    """Register this client's time and trigger Berkeley synchronization"""
    print("=" * 80)
    print("👑 MANUAL VIP CONTROLLER - EMERGENCY VEHICLE DISPATCHER 🚨")
    print("🚁 MANUAL VIP GENERATION & SIGNAL STATUS MONITOR")
    print("⚡ CREATE VIP REQUESTS FOR EMERGENCY VEHICLES")
    print("🎯 VIEW REAL-TIME SIGNAL STATUS ARRAY")
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
    
    print("🔗 Connecting to VIP-Enhanced Signal Manipulator Server...")
    
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
    """Display system statistics"""
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
        print(f"   🚁 Emergency Vehicle Route: {route_number}")
        print(f"   ⏰ Request Timestamp: {relative_timestamp}")
        print(f"   🚨 Priority Level: HIGHEST")
        
        # Submit VIP request to server
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
                print(f"\n🚁 VIP SIGNAL CHANGE SEQUENCE FOR ROUTE {route_number}:")
                
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

def show_menu():
    """Display the main menu"""
    print("\n" + "=" * 60)
    print("👑 MANUAL VIP CONTROLLER MENU")
    print("=" * 60)
    print("1. 🚁 Create VIP Request for Route 1")
    print("2. 🚁 Create VIP Request for Route 2") 
    print("3. 🚁 Create VIP Request for Route 3")
    print("4. 🚁 Create VIP Request for Route 4")
    print("5. 📊 View Current Signal Status")
    print("6. 📈 View System Statistics")
    print("7. 🔄 Continuous Status Monitor (press Ctrl+C to stop)")
    print("8. ❌ Exit")
    print("=" * 60)

def continuous_monitor():
    """Continuously display signal status updates"""
    print("\n🔄 STARTING CONTINUOUS SIGNAL STATUS MONITOR")
    print("   Press Ctrl+C to return to main menu")
    print("   Updates every 2 seconds")
    
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
    
    while True:
        try:
            show_menu()
            choice = input("\n🎯 Select option (1-8): ").strip()
            
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
                print("👑 VIP Controller shutting down...")
                break
            else:
                print("❌ Invalid choice. Please select 1-8.")
                
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
    print("👑 VIP EMERGENCY VEHICLE CONTROLLER ACTIVE")
    print("🔗 Connected to Four-Way Signal Manipulator Server")
    print("🚨 VIP CAPABILITIES:")
    print("   ⚡ Manual VIP request generation")
    print("   🎯 Choose specific emergency vehicle routes (1-4)")
    print("   📊 Real-time signal status monitoring")
    print("   🚁 Highest priority processing for VIP requests")
    print("   🔒 Enhanced Ricart-Agrawala with VIP priority")
    print("📊 SIGNAL STATUS ARRAY: Synchronized across all clients")
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
        print("🔄 Check server connection...")