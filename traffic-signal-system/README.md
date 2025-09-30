# Traffic Signal Management System

A distributed traffic signal management system with VIP emergency vehicle priority, load balancing, and real-time synchronization across multiple servers and clients.

## 🚦 Features

- **Real-time Traffic Signal Control** with Green→Yellow→Red transitions (8-second cycles)
- **VIP Emergency Vehicle Priority** with automatic cycle override and 10-second timeout
- **Load Balanced Architecture** with primary/clone server redundancy
- **Professional GUI Interface** with manual controls and real-time monitoring
- **Multi-Device Deployment** support for distributed operation

## 📦 Installation

### Prerequisites
```bash
# Python 3.7+ required
pip install PyQt5
```

### Clone Repository
```bash
git clone https://github.com/yourusername/traffic-signal-system.git
cd traffic-signal-system
```

## 🚀 Quick Start

### Option 1: Single Device Setup (Local Testing)

**Step 1:** Start Load Balancer
```bash
python loader_t8.py
```

**Step 2:** Start Primary Server (in new terminal)
```bash
python server_t8_1.py
# Enter time when prompted: 14:30:00
```

**Step 3:** Start Clone Server (in new terminal)
```bash
python sever_clone_t8_1.py
# Enter time when prompted: 14:30:00
```

**Step 4:** Launch Main Interface (in new terminal)
```bash
python ui.py
```

**Step 5:** Optional - Start Additional Clients
```bash
python client_t8.py        # Vehicle controller
python ps_t8.py            # Pedestrian monitor  
python manual_t8_1.py      # VIP emergency control
```

### Option 2: Multi-Device Setup (Network Deployment)

**Before Starting:** Update IP addresses in configuration files

#### Device 1 - Main Server (e.g., 192.168.1.100)
```bash
# 1. Edit loader_t8.py - Update server URLs:
self.servers = [
    {"url": "http://192.168.1.100:8000/"},  # Primary server IP
    {"url": "http://192.168.1.101:8001/"}   # Clone server IP
]

# 2. Start services
python loader_t8.py
python server_t8_1.py  # Enter time: 14:30:00
```

#### Device 2 - Clone Server (e.g., 192.168.1.101)
```bash
python sever_clone_t8_1.py  # Enter time: 14:30:00
```

#### Device 3 - Control Station (e.g., 192.168.1.102)
```bash
# Edit all client files (ui.py, client_t8.py, ps_t8.py, manual_t8_1.py)
# Update this line in each file:
server = xmlrpc.client.ServerProxy("http://192.168.1.100:9000/", allow_none=True)

# Start applications
python ui.py
python ps_t8.py
python manual_t8_1.py
```

#### Device 4 - Vehicle Controllers (e.g., 192.168.1.103)
```bash
# Update client_t8.py IP address (same as above)
python client_t8.py
```

#### Firewall Configuration
Open these ports on all devices:
- **Port 8000** - Primary Server
- **Port 8001** - Clone Server
- **Port 9000** - Load Balancer

## 🔧 System Components

### Core Files
- **`server_t8_1.py`** - Primary traffic signal server (Port 8000)
- **`sever_clone_t8_1.py`** - Backup server for redundancy (Port 8001)
- **`loader_t8.py`** - Load balancer routing requests (Port 9000)
- **`ui.py`** - Main graphical interface with VIP controls

### Client Applications
- **`client_t8.py`** - Vehicle signal requests
- **`ps_t8.py`** - Pedestrian signal monitoring
- **`manual_t8_1.py`** - VIP emergency vehicle control

## 🚨 Usage

### Normal Operation
- System cycles every 8 seconds: Green (0-5s) → Yellow (5-8s) → Red
- North-South and East-West signals alternate
- Pedestrian signals show opposite of vehicle signals

### VIP Emergency Mode
1. Click any **"VIP Signal X"** button in the main UI
2. Selected signal immediately turns GREEN
3. All other signals turn RED
4. Auto-cycling stops for 10 seconds
5. System automatically resumes normal operation

### Manual Control (RTO)
1. Click **"RTO Manual Control"** to stop auto-cycling
2. Use individual signal buttons to control lights
3. Click **"RTO Recycle"** to return to automatic mode

### Load Testing
- Run `manual_t8_1.py` and select option 8 for load testing
- Sends 15 concurrent requests to test system capacity

## 📊 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   Client Apps   │    │   Client Apps   │
│  ui.py          │    │ client_t8.py    │    │ manual_t8_1.py  │
│  ps_t8.py       │    │                 │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Load Balancer        │
                    │    loader_t8.py         │
                    │    Port: 9000           │
                    │  ┌─────────────────────┐│
                    │  │ Request Routing     ││
                    │  │ • Primary: 10 req   ││
                    │  │ • Clone: 10 req     ││
                    │  │ • Failover Support  ││
                    │  └─────────────────────┘│
                    └────────────┬────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
    ┌───────────▼───────────┐    │    ┌───────────▼───────────┐
    │   Primary Server      │    │    │   Clone Server        │
    │   server_t8_1.py      │    │    │   sever_clone_t8_1.py │
    │   Port: 8000          │    │    │   Port: 8001          │
    │ ┌───────────────────┐ │    │    │ ┌───────────────────┐ │
    │ │ Signal Control    │ │    │    │ │ Backup Processing │ │
    │ │ • 8s Auto Cycle   │ │    │    │ │ • Load Distribution│ │
    │ │ • Yellow Transitions│ │  │    │ │ • Time Sync       │ │
    │ │ • VIP Override    │ │    │    │ │ • Failover Ready  │ │
    │ │ • Ricart-Agrawala │ │    │    │ │ • Status Mirror   │ │
    │ └───────────────────┘ │    │    │ └───────────────────┘ │
    └───────────────────────┘    │    └───────────────────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         │             Shared Resources                  │
         │  ┌─────────────────────────────────────────┐  │
         │  │ Traffic Signal Status Array             │  │
         │  │ • t1,t2,t3,t4 (North,East,South,West)  │  │
         │  │ • p1,p2,p3,p4 (Pedestrian Signals)     │  │
         │  │ • VIP Priority Queue & Timeout         │  │
         │  │ • Berkeley Time Synchronization        │  │
         │  └─────────────────────────────────────────┘  │
         └───────────────────────────────────────────────┘
```

**Data Flow:**
1. **Clients** → Send requests to **Load Balancer** (Port 9000)
2. **Load Balancer** → Routes to **Primary** (8000) or **Clone** (8001) 
3. **Servers** → Process signal requests and VIP emergencies
4. **Servers** → Update shared signal status and sync time
5. **Clients** → Receive real-time status updates

## 🐛 Troubleshooting

### Common Issues

**Connection Failed:**
```
Error: Connection refused to 127.0.0.1:9000
Solution: Ensure load balancer is running first
```

**Time Sync Problems:**
```
Error: Berkeley synchronization failed  
Solution: Use same time format (HH:MM:SS) for both servers
```

**VIP Not Working:**
```
Error: VIP button not responding
Solution: Check server connections and try restarting servers
```

**Multi-Device Issues:**
```
Error: Cannot connect to remote server
Solution: 
1. Verify IP addresses in configuration files
2. Check firewall ports (8000, 8001, 9000)
3. Test network connectivity with ping
```

## 🔍 Configuration Details

### Network Setup Checklist
- [ ] Update IP addresses in `loader_t8.py`
- [ ] Update client connection URLs in all client files
- [ ] Open firewall ports 8000, 8001, 9000
- [ ] Test network connectivity between devices
- [ ] Start services in order: loader → primary server → clone server → clients

### Signal Timing Configuration
```python
# In server files, modify these values:
signal_cycle_interval = 8    # Total cycle time (seconds)
GREEN_PHASE = 5.0           # Green duration (0-5 seconds)
YELLOW_PHASE = 3.0          # Yellow duration (5-8 seconds)
vip_duration = 10           # VIP override timeout
```

## 📝 System Requirements

- **Python:** 3.7 or higher
- **OS:** Windows, Linux, or macOS
- **Network:** TCP/IP connectivity for multi-device setup
- **Memory:** 512MB RAM minimum
- **Ports:** 8000, 8001, 9000 available

---

**Ready to manage traffic signals like a pro! 🚦**