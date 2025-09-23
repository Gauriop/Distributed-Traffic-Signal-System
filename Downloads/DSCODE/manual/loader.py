import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer
import threading
import time
from collections import defaultdict

class LoadBalancer:
    def __init__(self):
        self.servers = [
            {"url": "http://127.0.0.1:8000/", "active_requests": 0, "max_requests": 10},
            {"url": "http://127.0.0.1:8001/", "active_requests": 0, "max_requests": 10}
        ]
        self.current_server_index = 0
        self.lock = threading.Lock()
        self.total_requests = 0
        self.load_balanced_requests = 0
        
    def get_available_server(self):
        """Get the server with least load or next available server"""
        with self.lock:
            # First try primary server if it has capacity
            if self.servers[0]["active_requests"] < self.servers[0]["max_requests"]:
                return 0
            
            # If primary is full, try secondary
            if self.servers[1]["active_requests"] < self.servers[1]["max_requests"]:
                self.load_balanced_requests += 1
                print(f"🔄 LOAD BALANCING: Redirecting request to server_clone (Request #{self.total_requests + 1})")
                return 1
            
            # Both servers full - return primary (will queue or reject)
            print(f"⚠️ OVERLOAD: Both servers at capacity! Using primary server")
            return 0
    
    def increment_server_load(self, server_index):
        """Increment active request count for a server"""
        with self.lock:
            self.servers[server_index]["active_requests"] += 1
            self.total_requests += 1
            print(f"📊 Server {server_index} load: {self.servers[server_index]['active_requests']}/{self.servers[server_index]['max_requests']}")
    
    def decrement_server_load(self, server_index):
        """Decrement active request count for a server"""
        with self.lock:
            if self.servers[server_index]["active_requests"] > 0:
                self.servers[server_index]["active_requests"] -= 1
    
    def get_server_proxy(self, server_index):
        """Get XML-RPC proxy for specified server"""
        try:
            return xmlrpc.client.ServerProxy(self.servers[server_index]["url"], allow_none=True)
        except Exception as e:
            print(f"❌ Failed to connect to server {server_index}: {e}")
            return None
    
    def route_request(self, method_name, *args, **kwargs):
        """Route request to appropriate server"""
        server_index = self.get_available_server()
        server_proxy = self.get_server_proxy(server_index)
        
        if not server_proxy:
            return None
        
        try:
            self.increment_server_load(server_index)
            
            # Get the method from the server proxy
            method = getattr(server_proxy, method_name)
            result = method(*args, **kwargs)
            
            return result
        except Exception as e:
            print(f"❌ Error routing {method_name} to server {server_index}: {e}")
            return None
        finally:
            # Simulate request completion delay
            threading.Timer(3.0, lambda: self.decrement_server_load(server_index)).start()
    
    def get_load_balancer_stats(self):
        """Return load balancer statistics"""
        with self.lock:
            return {
                "total_requests": self.total_requests,
                "load_balanced_requests": self.load_balanced_requests,
                "server_0_load": f"{self.servers[0]['active_requests']}/{self.servers[0]['max_requests']}",
                "server_1_load": f"{self.servers[1]['active_requests']}/{self.servers[1]['max_requests']}",
                "server_0_url": self.servers[0]["url"],
                "server_1_url": self.servers[1]["url"]
            }

# Global load balancer instance
load_balancer = LoadBalancer()

# Wrapper functions for all the original server methods
def signal_manipulator(requested_signal):
    return load_balancer.route_request("signal_manipulator", requested_signal)

def vip_signal_manipulator(requested_signal):
    return load_balancer.route_request("vip_signal_manipulator", requested_signal)

def submit_vip_requests(vip_data):
    return load_balancer.route_request("submit_vip_requests", vip_data)

def get_next_message():
    return load_balancer.route_request("get_next_message")

def get_next_pedestrian_message():
    return load_balancer.route_request("get_next_pedestrian_message")

def register_client_time(client_id, time_input):
    return load_balancer.route_request("register_client_time", client_id, time_input)

def berkeley_synchronization():
    return load_balancer.route_request("berkeley_synchronization")

def get_synchronized_time():
    return load_balancer.route_request("get_synchronized_time")

def get_active_signal():
    return load_balancer.route_request("get_active_signal")

def get_system_stats():
    # Combine system stats with load balancer stats
    system_stats = load_balancer.route_request("get_system_stats")
    lb_stats = load_balancer.get_load_balancer_stats()
    
    if system_stats:
        system_stats.update(lb_stats)
    
    return system_stats

def get_signal_status():
    return load_balancer.route_request("get_signal_status")

if __name__ == "__main__":
    print("=" * 80)
    print("🔄 LOAD BALANCER - TRAFFIC SIGNAL SYSTEM")
    print("📊 SERVER CAPACITY: 10 requests per server")
    print("🔀 AUTO-ROUTING: Primary (8000) → Clone (8001)")
    print("⚖️ LOAD BALANCING: Distributes traffic when primary is full")
    print("=" * 80)
    
    print("🔗 Starting Load Balancer on port 9000...")
    print("📡 Routing to:")
    print(f"   Primary Server: http://192.168.1.100:8000/ (Max: 10 requests)")
    print(f"   Clone Server:   http://192.168.1.100:8001/ (Max: 10 requests)")
    print("=" * 80)
    
    # server = SimpleXMLRPCServer(("0.0.0.0", 9000), allow_none=True)
    server = SimpleXMLRPCServer(("127.0.0.1", 9000), allow_none=True)
    
    # Register all the wrapper functions
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
    
    print("🔄 Load Balancer ready! Waiting for client connections...")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Load Balancer stopped manually.")
        stats = load_balancer.get_load_balancer_stats()
        print("\n📈 LOAD BALANCER STATISTICS:")
        print(f"   Total requests handled: {stats['total_requests']}")
        print(f"   Load balanced requests: {stats['load_balanced_requests']}")
        print(f"   Server 0 final load: {stats['server_0_load']}")
        print(f"   Server 1 final load: {stats['server_1_load']}")