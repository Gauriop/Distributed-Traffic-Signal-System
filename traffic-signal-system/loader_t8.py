import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import threading
import time
import socket
from collections import defaultdict

class ThreadedXMLRPCRequestHandler(SimpleXMLRPCRequestHandler):
    """Custom request handler with timeout handling"""
    timeout = 60
    
    def setup(self):
        """Setup with socket timeout"""
        SimpleXMLRPCRequestHandler.setup(self)
        self.request.settimeout(self.timeout)

class LoadBalancer:
    def __init__(self):
        self.servers = [
            {
                "url": "http://127.0.0.1:8000/", 
                "active_requests": 0, 
                "max_requests": 10,
                "connection_pool": [],
                "failed_attempts": 0,
                "last_failure": None
            },
            {
                "url": "http://127.0.0.1:8001/", 
                "active_requests": 0, 
                "max_requests": 10,
                "connection_pool": [],
                "failed_attempts": 0,
                "last_failure": None
            }
        ]
        self.lock = threading.Lock()
        self.total_requests = 0
        self.load_balanced_requests = 0
        self.failed_requests = 0
        self.timeout_requests = 0
        self.retry_attempts = 0
        
    def create_server_connection(self, server_index, timeout=60):
        """Create a new server connection with proper timeout"""
        try:
            server_url = self.servers[server_index]["url"]
            
            # Create transport with timeout
            transport = xmlrpc.client.Transport(use_datetime=True)
            transport.timeout = timeout
            
            proxy = xmlrpc.client.ServerProxy(
                server_url, 
                allow_none=True,
                transport=transport,
                verbose=False
            )
            
            return proxy
        except Exception as e:
            print(f"❌ Failed to create connection to server {server_index}: {e}")
            return None
    
    def get_server_connection(self, server_index):
        """Get a connection from pool or create new one"""
        server_info = self.servers[server_index]
        
        # Check if server is temporarily failed
        if (server_info["failed_attempts"] > 3 and 
            server_info["last_failure"] and 
            time.time() - server_info["last_failure"] < 30):
            return None
        
        # Try to reuse existing connection from pool
        if server_info["connection_pool"]:
            return server_info["connection_pool"].pop()
        
        # Create new connection
        return self.create_server_connection(server_index)
    
    def return_connection_to_pool(self, server_index, connection):
        """Return connection to pool for reuse"""
        if connection and len(self.servers[server_index]["connection_pool"]) < 5:
            self.servers[server_index]["connection_pool"].append(connection)
    
    def mark_server_failure(self, server_index, error):
        """Mark server as failed temporarily"""
        with self.lock:
            self.servers[server_index]["failed_attempts"] += 1
            self.servers[server_index]["last_failure"] = time.time()
            self.failed_requests += 1
            print(f"⚠️ Server {server_index} failed - {error}")
    
    def mark_server_success(self, server_index):
        """Mark server as successful, reset failure counter"""
        with self.lock:
            self.servers[server_index]["failed_attempts"] = 0
            self.servers[server_index]["last_failure"] = None
    
    def get_available_server(self):
        """Simple logic: Use primary server unless it's overloaded, then use secondary"""
        with self.lock:
            primary_load = self.servers[0]["active_requests"]
            primary_max = self.servers[0]["max_requests"]
            primary_healthy = self.servers[0]["failed_attempts"] <= 3
            
            secondary_healthy = self.servers[1]["failed_attempts"] <= 3
            
            print(f"🔍 Primary server: {primary_load}/{primary_max} requests")
            
            # Use primary server if it has capacity and is healthy
            if primary_load < primary_max and primary_healthy:
                print(f"✅ Using PRIMARY server")
                return 0
            
            # Primary is overloaded or unhealthy - use secondary if available
            elif secondary_healthy:
                print(f"🔄 PRIMARY OVERLOADED ({primary_load}/{primary_max}) - Using SECONDARY server")
                self.load_balanced_requests += 1
                return 1
            
            # Both servers have issues - try primary anyway
            else:
                print(f"⚠️ Both servers have issues - trying PRIMARY")
                return 0
    
    def increment_server_load(self, server_index):
        """Increment active request count for a server"""
        with self.lock:
            self.servers[server_index]["active_requests"] += 1
            self.total_requests += 1
            current_load = self.servers[server_index]["active_requests"]
            max_load = self.servers[server_index]["max_requests"]
            print(f"📈 Server {server_index} load: {current_load}/{max_load}")
    
    def decrement_server_load(self, server_index):
        """Decrement active request count for a server"""
        with self.lock:
            if self.servers[server_index]["active_requests"] > 0:
                self.servers[server_index]["active_requests"] -= 1
                current_load = self.servers[server_index]["active_requests"]
                max_load = self.servers[server_index]["max_requests"]
                print(f"📉 Server {server_index} load: {current_load}/{max_load}")
    
    def route_request_with_retry(self, method_name, *args, **kwargs):
        """Route request with retry logic and error handling"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            server_index = self.get_available_server()
            if server_index is None:
                return None
            
            connection = self.get_server_connection(server_index)
            if not connection:
                retry_count += 1
                continue
            
            # Increment load BEFORE making the request
            self.increment_server_load(server_index)
            
            try:
                # Execute method
                method = getattr(connection, method_name)
                start_time = time.time()
                result = method(*args, **kwargs)
                end_time = time.time()
                
                # Mark server as successful
                self.mark_server_success(server_index)
                
                # Return connection to pool for reuse
                self.return_connection_to_pool(server_index, connection)
                
                # Log successful request
                duration = end_time - start_time
                print(f"✅ {method_name} completed in {duration:.2f}s on server {server_index}")
                
                # Schedule load decrement after 20 seconds (realistic processing time)
                threading.Timer(4.0, lambda: self.decrement_server_load(server_index)).start()
                
                return result
                
            except socket.timeout:
                self.timeout_requests += 1
                print(f"⏱️ TIMEOUT: {method_name} on server {server_index}")
                self.mark_server_failure(server_index, "timeout")
                
            except xmlrpc.client.Fault as e:
                print(f"⚠️ XML-RPC FAULT: {method_name} on server {server_index}: {e}")
                self.mark_server_failure(server_index, f"xml-rpc fault: {e}")
                
            except ConnectionError as e:
                print(f"🔌 CONNECTION ERROR: {method_name} on server {server_index}: {e}")
                self.mark_server_failure(server_index, f"connection error: {e}")
                
            except Exception as e:
                print(f"💥 ERROR: {method_name} on server {server_index}: {e}")
                self.mark_server_failure(server_index, f"error: {e}")
            
            finally:
                # If request failed, decrement load immediately
                if retry_count > 0:
                    self.decrement_server_load(server_index)
            
            retry_count += 1
            self.retry_attempts += 1
            
            if retry_count < max_retries:
                print(f"🔄 RETRY {retry_count + 1}/{max_retries}")
                time.sleep(0.5 * retry_count)
        
        # All retries failed - decrement load
        if server_index is not None:
            self.decrement_server_load(server_index)
        
        print(f"❌ {method_name} failed after {max_retries} attempts")
        return None
    
    def get_load_balancer_stats(self):
        """Return load balancer statistics"""
        with self.lock:
            return {
                "total_requests": self.total_requests,
                "load_balanced_requests": self.load_balanced_requests,
                "failed_requests": self.failed_requests,
                "timeout_requests": self.timeout_requests,
                "retry_attempts": self.retry_attempts,
                "server_0_load": f"{self.servers[0]['active_requests']}/{self.servers[0]['max_requests']}",
                "server_1_load": f"{self.servers[1]['active_requests']}/{self.servers[1]['max_requests']}",
                "server_0_failures": self.servers[0]["failed_attempts"],
                "server_1_failures": self.servers[1]["failed_attempts"],
                "server_0_url": self.servers[0]["url"],
                "server_1_url": self.servers[1]["url"]
            }

# Global load balancer instance
load_balancer = LoadBalancer()

# Wrapper functions for all the original server methods
def signal_manipulator(requested_signal):
    result = load_balancer.route_request_with_retry("signal_manipulator", requested_signal)
    return result if result is not None else False

def vip_signal_manipulator(requested_signal):
    result = load_balancer.route_request_with_retry("vip_signal_manipulator", requested_signal)
    return result if result is not None else False

def submit_vip_requests(vip_data):
    result = load_balancer.route_request_with_retry("submit_vip_requests", vip_data)
    return result if result is not None else False

def get_next_message():
    result = load_balancer.route_request_with_retry("get_next_message")
    return result

def get_next_pedestrian_message():
    result = load_balancer.route_request_with_retry("get_next_pedestrian_message")
    return result

def register_client_time(client_id, time_input):
    result = load_balancer.route_request_with_retry("register_client_time", client_id, time_input)
    return result if result is not None else False

def berkeley_synchronization():
    result = load_balancer.route_request_with_retry("berkeley_synchronization")
    return result

def get_synchronized_time():
    result = load_balancer.route_request_with_retry("get_synchronized_time")
    return result

def get_active_signal():
    result = load_balancer.route_request_with_retry("get_active_signal")
    return result if result is not None else 1

def get_system_stats():
    system_stats = load_balancer.route_request_with_retry("get_system_stats")
    lb_stats = load_balancer.get_load_balancer_stats()
    
    if system_stats:
        system_stats.update(lb_stats)
        return system_stats
    else:
        return lb_stats

def get_signal_status():
    result = load_balancer.route_request_with_retry("get_signal_status")
    if result is None:
        return {
            "t1": "green", "t2": "red", "t3": "red", "t4": "red",
            "p1": "red", "p2": "green", "p3": "green", "p4": "green"
        }
    return result

def get_countdown_info():
    result = load_balancer.route_request_with_retry("get_countdown_info")
    if result is None:
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
    return result

if __name__ == "__main__":
    print("=" * 60)
    print("🔄 SIMPLE LOAD BALANCER - TRAFFIC SIGNAL SYSTEM")
    print("📊 Logic: Use PRIMARY server until overloaded, then use SECONDARY")
    print("🔀 PRIMARY: http://127.0.0.1:8000/ (Max: 10 requests)")
    print("🔀 SECONDARY: http://127.0.0.1:8001/ (Max: 10 requests)")
    print("=" * 60)
    
    try:
        server = SimpleXMLRPCServer(
            ("127.0.0.1", 9000), 
            allow_none=True,
            requestHandler=ThreadedXMLRPCRequestHandler
        )
        
        server.socket.settimeout(60)
        
        # Register all functions
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
        
        print("🚀 Simple Load Balancer ready on port 9000!")
        print("💡 Send 11+ concurrent requests to see load balancing!")
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Load Balancer stopped.")
        stats = load_balancer.get_load_balancer_stats()
        print(f"\n📈 STATS:")
        print(f"   Total requests: {stats['total_requests']}")
        print(f"   Load balanced: {stats['load_balanced_requests']}")
        print(f"   Current loads: P={stats['server_0_load']}, S={stats['server_1_load']}")
    except Exception as e:
        print(f"❌ Load Balancer error: {e}")
        print("💡 Check that servers are running on ports 8000 and 8001")