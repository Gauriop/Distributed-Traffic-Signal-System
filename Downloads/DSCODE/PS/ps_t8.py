import xmlrpc.client
import time

# UPDATED TO CONNECT TO LOAD BALANCER ON PORT 9000
# server = xmlrpc.client.ServerProxy("http://192.168.1.200:9000/", allow_none=True)
server = xmlrpc.client.ServerProxy("http://127.0.0.1:9000/", allow_none=True)

def register_time_and_sync():
    """Register this client's time and trigger Berkeley synchronization"""
    print("=" * 80)
    print("🚶‍♂️ FOUR-WAY PEDESTRIAN CONTROLLER - LOAD BALANCED VERSION 🚶‍♀️")
    print("📊 CONNECTED TO LOAD BALANCER (PORT 9000)")
    print("⚖️ LOAD BALANCER DISTRIBUTES TO PRIMARY (8000) & CLONE (8001)")
    print("🚶‍♂️ MONITORING PEDESTRIAN CROSSINGS & SIGNAL STATUS")
    print("⚡ MONITORING PEDESTRIAN CROSSINGS (OPPOSITE TO VEHICLE SIGNALS)")
    print("🚨 VIP vehicles handled by tm.py with HIGHER PRIORITY")
    print("👑 VIPs processed FIRST, then regular requests in same cycle")
    print("📊 Shows real-time signal status array (on request)")
    print("=" * 80)
    
    while True:
        pedestrian_time = input("🕕 Enter Pedestrian Signal time (HH:MM:SS): ")
        try:
            hour, minute, second = map(int, pedestrian_time.split(':'))
            if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                break
            else:
                print("❌ Invalid time values. Please use valid HH:MM:SS format.")
        except:
            print("❌ Invalid time format. Please use HH:MM:SS")
    
    print("🔗 Connecting to Load Balancer...")
    
    try:
        success = server.register_client_time("Pedestrian Signal", pedestrian_time)
        if success:
            print("✅ Pedestrian Signal time registered successfully!")
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
    """Display current signal status array"""
    try:
        status = server.get_signal_status()
        print("📊 CURRENT SIGNAL STATUS:")
        print(f"   Traffic:     T1:{status['t1']} | T2:{status['t2']} | T3:{status['t3']} | T4:{status['t4']}")
        print(f"   Pedestrian:  P1:{status['p1']} | P2:{status['p2']} | P3:{status['p3']} | P4:{status['p4']}")
    except Exception as e:
        print(f"❌ Failed to get signal status: {e}")

def p_signal():
    """Monitor four-way pedestrian crossing signals with VIP awareness"""
    print("🚶‍♂️ Monitoring four-way pedestrian crossing signals via Load Balancer...")
    print("🔄 Pedestrian signals change when vehicle signals change (mutual exclusion)")
    print("⚡ When vehicle signal X turns GREEN → Pedestrian crossing X turns RED")
    print("⚡ When vehicle signal X turns RED → Pedestrian crossing X turns GREEN")
    print("👑 VIP PRIORITY: Emergency vehicles cause immediate pedestrian signal changes!")
    print("🚨 VIP crossing = Pedestrians must IMMEDIATELY stop for emergency vehicles")
    print("🎯 KEY: Signal trying to turn GREEN = Pedestrian crossing turns RED")
    print("📡 All signals routed through Load Balancer for high availability")
    
    try:
        message_count = 0
        vip_alert_shown = False
        
        while True:
            msg = server.get_next_pedestrian_message()
            if msg is None:
                # Sleep briefly and check again, but don't print anything
                time.sleep(0.5)
                continue
            
            message_count += 1
            
            # Enhanced display for VIP-related messages - only show VIP was involved in processing
            if "VIP" in msg or "👑" in msg:
                if not vip_alert_shown:
                    print(f"\n🚨 VIP PRIORITY PROCESSING DETECTED!")
                    print(f"🚶‍♂️ VIP requests were processed with higher priority!")
                    print(f"📡 Load Balancer routed VIP emergency request!")
                    vip_alert_shown = True
                
                # Remove VIP-specific content, show normal pedestrian messages
                clean_msg = msg.replace("VIP PRIORITY: ", "").replace("👑 VIP PRIORITY: ", "").replace("🚨 VIP PRIORITY: ", "").replace("🚶‍♂️ VIP PRIORITY: ", "").replace("🚶‍♀️ VIP PRIORITY: ", "")
                # Remove clone server identifiers for clean display
                clean_msg = clean_msg.replace("CLONE - ", "")
                print(f"🚶‍♂️ PEDESTRIAN: {clean_msg}")
                
                # Reset VIP alert after processing VIP messages
                if "VIP" not in msg and "👑" not in msg:
                    vip_alert_shown = False
            else:
                # Remove clone server identifiers for clean display
                clean_msg = msg.replace("CLONE - ", "")
                print(f"🚶‍♂️ PEDESTRIAN: {clean_msg}")
                vip_alert_shown = False

    except Exception as e:
        print("❌ Error communicating with load balancer:", e)

def display_status():
    """Display current synchronized time, signal status, and VIP system status"""
    try:
        sync_time = server.get_synchronized_time()
        active_signal = server.get_active_signal()
        stats = server.get_system_stats()
        
        if sync_time:
            print(f"⏰ Current synchronized time: {sync_time}")
        if active_signal:
            print(f"🚗 Vehicle signal currently GREEN: {active_signal}")
            print(f"🚶‍♀️ Pedestrian crossing currently RED: {active_signal}")
            
            pedestrian_green = [sig for sig in [1, 2, 3, 4] if sig != active_signal]
            if pedestrian_green:
                print(f"🚶‍♂️ Pedestrian crossings currently GREEN: {pedestrian_green}")
        
        # Display VIP system status
        if stats:
            print(f"\n👑 VIP SYSTEM STATUS:")
            if stats.get('vip_processing', False):
                print(f"   🚨 VIP emergency processing ACTIVE - pedestrians be alert!")
            else:
                print(f"   ✅ VIP system monitoring - ready for emergency vehicles")
            
            vip_total = stats.get('vip_requests_processed', 0)
            total_requests = stats.get('total_requests_processed', 0)
            
            if vip_total > 0:
                print(f"   📊 VIP requests handled: {vip_total}/{total_requests}")
                print(f"   🚶‍♂️ Pedestrians have responded to {vip_total} VIP emergencies")
            
            if stats.get('vip_pending_requests', 0) > 0:
                print(f"   ⚠️ VIP requests pending: {stats['vip_pending_requests']}")
                print(f"   🚶‍♀️ Pedestrians should prepare for signal changes!")
            
            # Load balancer specific info
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
    print("🚦 FOUR-WAY INTERSECTION - LOAD BALANCED PEDESTRIAN CONTROLLER")
    print("📡 CONNECTED TO LOAD BALANCER (PORT 9000)")
    print("⚖️ LOAD BALANCING:")
    print("   🟦 Primary Server: http://127.0.0.1:8000/ (Capacity: 10)")
    print("   🟨 Clone Server:   http://127.0.0.1:8001/ (Capacity: 10)")
    print("   📊 Total System Capacity: 20 simultaneous requests")
    print("🔄 PEDESTRIAN SIGNAL LOGIC (Opposite to Vehicle Signals):")
    print("   🟢 When Vehicle Signal X is RED  → Pedestrian Crossing X is GREEN")
    print("   🔴 When Vehicle Signal X is GREEN → Pedestrian Crossing X is RED")
    print("👑 VIP EMERGENCY PRIORITY:")
    print("   🚨 VIP vehicles get immediate GREEN → Pedestrian crossing immediately RED")
    print("   ⚡ Faster signal changes for emergency vehicles")
    print("   🚶‍♂️ Pedestrians must respond quickly to VIP priority changes")
    print("🔒 Enhanced Ricart-Agrawala ensures coordinated signal changes")
    print("⚡ Only ONE vehicle signal GREEN at a time = THREE pedestrian crossings GREEN")
    print("🎲 VIP Generation: Manual control via tm.py")
    print("📊 Signal Status Array: Shown at startup and on request")
    print("📡 High Availability: Automatic failover between servers")
    print("=" * 80)
    
    # Display status once at startup
    display_status()
    
    try:
        # Run the pedestrian signal controller
        p_signal()
    except KeyboardInterrupt:
        print("\n🛑 Load-balanced four-way pedestrian signal monitor stopped manually.")
        
        # Show final VIP statistics
        try:
            stats = server.get_system_stats()
            if stats and stats.get('vip_requests_processed', 0) > 0:
                print(f"\n📊 FINAL VIP STATISTICS:")
                print(f"   Total VIP emergencies handled: {stats['vip_requests_processed']}")
                print(f"   Pedestrian responses to VIP: {stats['vip_requests_processed']}")
                print(f"   🚶‍♂️ Thank you for responding to emergency vehicles!")
                
                # Load balancer final stats
                if 'total_requests' in stats:
                    print(f"\n📡 LOAD BALANCER FINAL STATS:")
                    print(f"   Total requests routed: {stats['total_requests']}")
                    print(f"   Load balanced requests: {stats['load_balanced_requests']}")
        except:
            pass
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("🔄 Retrying connection to load balancer...")
        time.sleep(5)