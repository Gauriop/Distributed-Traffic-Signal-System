import sys
import xmlrpc.client
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                            QGroupBox, QSplitter, QStatusBar, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPolygon, QFont, QLinearGradient
import time
import random
import math
from datetime import datetime

class TrafficLight:
    """Traffic light class with position and state"""
    
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction
        self.red = True
        self.yellow = False
        self.green = False
        self.pedestrian_red = True
        self.pedestrian_green = False
    
    def set_state(self, red=False, yellow=False, green=False):
        """Set traffic light state"""
        self.red = red
        self.yellow = yellow
        self.green = green
        self.pedestrian_red = not green
        self.pedestrian_green = green

class TrafficSimulationWidget(QWidget):
    """Main widget for the traffic simulation display with modern styling, roads, cars, and pedestrians"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
                border-radius: 10px;
            }
        """)
        
        # Simulation parameters
        self.traffic_lights = {}
        self.intersection_center = QPoint(400, 300)
        self.road_width = 120
        self.lane_width = 30
        
        # VIP visual indicators
        self.vip_active = False
        self.vip_signal_id = None
        self.vip_flash_timer = 0
        
        # RTO manual control mode
        self.rto_mode = False
        self.manual_signal_states = {
            "north": {"traffic": "red", "pedestrian": "green"},
            "east": {"traffic": "red", "pedestrian": "green"}, 
            "south": {"traffic": "red", "pedestrian": "green"},
            "west": {"traffic": "red", "pedestrian": "green"}
        }
        
        # Countdown information for server sync
        self.countdown_info = {
            "time_remaining": 0,
            "current_pair": "North-South",
            "next_pair": "East-West",
            "current_green_signals": [1, 3],
            "next_green_signals": [2, 4],
            "cycle_interval": 8,
            "signal_status": {}
        }
        
        # Car and pedestrian animation parameters
        self.cars = {
            "north": {"position": -200, "speed": 5, "active": False},
            "south": {"position": 200, "speed": -5, "active": False},
            "east": {"position": 200, "speed": -5, "active": False},
            "west": {"position": -200, "speed": 5, "active": False}
        }
        self.pedestrians = {
            "north": {"position": 0, "speed": 2, "active": False, "count": 0},
            "south": {"position": 0, "speed": -2, "active": False, "count": 0},
            "east": {"position": 0, "speed": 2, "active": False, "count": 0},
            "west": {"position": 0, "speed": -2, "active": False, "count": 0}
        }
        
        # Initialize traffic lights
        self.setup_traffic_lights()
        
        # Animation timer for repainting
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animations)
        self.animation_timer.start(100)
    
    def setup_traffic_lights(self):
        """Setup traffic lights in grid layout - centered and bigger"""
        center_x = 400
        center_y = 300
        spacing = 200
        
        self.traffic_lights = {
            "north": TrafficLight(center_x, center_y - spacing, "north"),
            "south": TrafficLight(center_x, center_y + spacing, "south"),
            "east": TrafficLight(center_x + spacing, center_y, "east"),
            "west": TrafficLight(center_x - spacing, center_y, "west")
        }
        
        # Initially set north-south to green
        self.traffic_lights["north"].set_state(green=True)
        self.traffic_lights["south"].set_state(green=True)
    
    def update_traffic_lights(self, signal_status):
        """Update traffic light states from server with proper 4-way intersection logic"""
        if self.rto_mode:
            return
            
        signal_map = {"t1": "north", "t2": "east", "t3": "south", "t4": "west"}
        
        for signal_id, direction in signal_map.items():
            if signal_id in signal_status and direction in self.traffic_lights:
                state = signal_status[signal_id].lower()
                
                if state == "green":
                    self.traffic_lights[direction].set_state(green=True)
                    self.traffic_lights[direction].pedestrian_red = True
                    self.traffic_lights[direction].pedestrian_green = False
                    self.cars[direction]["active"] = True
                    self.pedestrians[direction]["active"] = False
                elif state == "yellow":
                    self.traffic_lights[direction].set_state(yellow=True)
                    self.traffic_lights[direction].pedestrian_red = True
                    self.traffic_lights[direction].pedestrian_green = False
                    self.cars[direction]["active"] = False
                    self.pedestrians[direction]["active"] = False
                else:
                    self.traffic_lights[direction].set_state(red=True)
                    self.traffic_lights[direction].pedestrian_red = False
                    self.traffic_lights[direction].pedestrian_green = True
                    self.cars[direction]["active"] = False
                    self.pedestrians[direction]["active"] = True
                    self.pedestrians[direction]["count"] = random.randint(1, 3)
    
    def update_countdown_info(self, countdown_info):
        """Update countdown information"""
        self.countdown_info = countdown_info
    
    def set_vip_active(self, signal_id):
        """Set VIP mode active for specific signal"""
        self.vip_active = True
        self.vip_signal_id = signal_id
        self.vip_flash_timer = 0
    
    def clear_vip_active(self):
        """Clear VIP active state"""
        self.vip_active = False
        self.vip_signal_id = None
        self.vip_flash_timer = 0
    
    def set_rto_mode(self, enabled):
        """Enable or disable RTO manual control mode"""
        self.rto_mode = enabled
        if enabled:
            print("RTO Mode: Manual control activated")
        else:
            print("RTO Mode: Auto-cycle resumed")
    
    def set_manual_signal_state(self, direction, signal_type, state):
        """Set manual signal state for RTO control"""
        if direction in self.manual_signal_states:
            self.manual_signal_states[direction][signal_type] = state
            
            if direction in self.traffic_lights:
                light = self.traffic_lights[direction]
                if signal_type == "traffic":
                    if state == "green":
                        light.set_state(green=True)
                        self.cars[direction]["active"] = True
                        self.pedestrians[direction]["active"] = False
                    elif state == "yellow":
                        light.set_state(yellow=True)
                        self.cars[direction]["active"] = False
                        self.pedestrians[direction]["active"] = False
                    else:
                        light.set_state(red=True)
                        self.cars[direction]["active"] = False
                        self.pedestrians[direction]["active"] = True
                        self.pedestrians[direction]["count"] = random.randint(1, 3)
                elif signal_type == "pedestrian":
                    if state == "green":
                        light.pedestrian_green = True
                        light.pedestrian_red = False
                        self.pedestrians[direction]["active"] = True
                        self.pedestrians[direction]["count"] = random.randint(1, 3)
                    else:
                        light.pedestrian_green = False
                        light.pedestrian_red = True
                        self.pedestrians[direction]["active"] = False
    
    def update_animations(self):
        """Update car and pedestrian positions for animation"""
        for direction in self.cars:
            if self.cars[direction]["active"]:
                self.cars[direction]["position"] += self.cars[direction]["speed"]
                # Reset car position when it moves off-screen
                if direction in ["north", "west"] and self.cars[direction]["position"] > 200:
                    self.cars[direction]["position"] = -200
                elif direction in ["south", "east"] and self.cars[direction]["position"] < -200:
                    self.cars[direction]["position"] = 200
        
        for direction in self.pedestrians:
            if self.pedestrians[direction]["active"]:
                self.pedestrians[direction]["position"] += self.pedestrians[direction]["speed"]
                # Reset pedestrian position when crossing is complete
                if abs(self.pedestrians[direction]["position"]) > self.road_width:
                    self.pedestrians[direction]["position"] = 0
                    self.pedestrians[direction]["active"] = False
                    self.pedestrians[direction]["count"] = 0
        
        self.update()
    
    def paintEvent(self, event):
        """Paint the traffic signals, roads, cars, and pedestrians with modern styling"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create gradient background
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(26, 26, 46))
        gradient.setColorAt(0.5, QColor(22, 33, 62))
        gradient.setColorAt(1, QColor(15, 52, 96))
        painter.fillRect(self.rect(), QBrush(gradient))
        
        # Draw roads and zebra crossings
        self.draw_roads_and_crossings(painter)
        
        # Draw cars
        self.draw_cars(painter)
        
        # Draw pedestrians
        self.draw_pedestrians(painter)
        
        # Draw modern traffic lights
        self.draw_traffic_lights(painter)
    
    def draw_roads_and_crossings(self, painter):
        """Draw roads and zebra crossings"""
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Draw asphalt roads
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        
        # Vertical road (North-South)
        painter.drawRect(center_x - self.road_width // 2, 0, self.road_width, self.height())
        
        # Horizontal road (East-West)
        painter.drawRect(0, center_y - self.road_width // 2, self.width(), self.road_width)
        
        # Draw lane markings
        painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.DashLine))
        painter.drawLine(center_x, 0, center_x, center_y - self.road_width // 2)
        painter.drawLine(center_x, center_y + self.road_width // 2, center_x, self.height())
        painter.drawLine(0, center_y, center_x - self.road_width // 2, center_y)
        painter.drawLine(center_x + self.road_width // 2, center_y, self.width(), center_y)
        
        # Draw zebra crossings
        zebra_width = 40
        stripe_height = 10
        stripe_spacing = 10
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        
        # North crossing
        for i in range(5):
            painter.drawRect(center_x - self.road_width // 2, center_y - self.road_width // 2 - zebra_width + i * (stripe_height + stripe_spacing), self.road_width, stripe_height)
        
        # South crossing
        for i in range(5):
            painter.drawRect(center_x - self.road_width // 2, center_y + self.road_width // 2 + i * (stripe_height + stripe_spacing), self.road_width, stripe_height)
        
        # East crossing
        for i in range(5):
            painter.drawRect(center_x + self.road_width // 2 + i * (stripe_height + stripe_spacing), center_y - self.road_width // 2, stripe_height, self.road_width)
        
        # West crossing
        for i in range(5):
            painter.drawRect(center_x - self.road_width // 2 - zebra_width + i * (stripe_height + stripe_spacing), center_y - self.road_width // 2, stripe_height, self.road_width)
    
    def draw_cars(self, painter):
        """Draw animated cars on the roads"""
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        painter.setPen(QPen(QColor(40, 40, 40), 2))
        car_width = 20
        car_height = 40
        
        for direction, car in self.cars.items():
            if not car["active"]:
                continue
            
            # Car color with modern metallic look
            car_gradient = QLinearGradient(0, 0, 0, car_height)
            car_gradient.setColorAt(0, QColor(100, 100, 120))
            car_gradient.setColorAt(0.5, QColor(60, 60, 80))
            car_gradient.setColorAt(1, QColor(40, 40, 60))
            painter.setBrush(QBrush(car_gradient))
            
            if direction == "north":
                x = center_x - self.lane_width // 2 - car_width // 2
                y = center_y - self.road_width // 2 + car["position"]
                painter.drawRoundedRect(x, y, car_width, car_height, 5, 5)
            elif direction == "south":
                x = center_x + self.lane_width // 2 - car_width // 2
                y = center_y + self.road_width // 2 + car["position"]
                painter.drawRoundedRect(x, y, car_width, car_height, 5, 5)
            elif direction == "east":
                x = center_x + self.road_width // 2 + car["position"]
                y = center_y - self.lane_width // 2 - car_width // 2
                painter.drawRoundedRect(x, y, car_height, car_width, 5, 5)
            elif direction == "west":
                x = center_x - self.road_width // 2 + car["position"]
                y = center_y + self.lane_width // 2 - car_width // 2
                painter.drawRoundedRect(x, y, car_height, car_width, 5, 5)
    
    def draw_pedestrians(self, painter):
        """Draw animated pedestrians on zebra crossings"""
        center_x = self.width() // 2
        center_y = self.height() // 2
        zebra_width = 40
        
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(QBrush(QColor(200, 200, 255)))
        
        ped_size = 10
        
        for direction, ped in self.pedestrians.items():
            if not ped["active"] or ped["count"] == 0:
                continue
                
            for i in range(ped["count"]):
                offset = i * 20  # Space out pedestrians
                
                if direction == "north":
                    x = center_x - self.road_width // 2 + offset
                    y = center_y - self.road_width // 2 - zebra_width // 2 + ped["position"]
                    painter.drawEllipse(x, y, ped_size, ped_size)
                elif direction == "south":
                    x = center_x - self.road_width // 2 + offset
                    y = center_y + self.road_width // 2 + zebra_width // 2 + ped["position"]
                    painter.drawEllipse(x, y, ped_size, ped_size)
                elif direction == "east":
                    x = center_x + self.road_width // 2 + zebra_width // 2 + ped["position"]
                    y = center_y - self.road_width // 2 + offset
                    painter.drawEllipse(x, y, ped_size, ped_size)
                elif direction == "west":
                    x = center_x - self.road_width // 2 - zebra_width // 2 + ped["position"]
                    y = center_y - self.road_width // 2 + offset
                    painter.drawEllipse(x, y, ped_size, ped_size)
    
    def draw_traffic_lights(self, painter):
        """Draw traffic lights with modern glass-morphism style"""
        actual_center_x = self.width() // 2
        actual_center_y = self.height() // 2
        spacing = 220
        
        # Update positions
        self.traffic_lights["north"].x = actual_center_x
        self.traffic_lights["north"].y = actual_center_y - spacing
        self.traffic_lights["south"].x = actual_center_x
        self.traffic_lights["south"].y = actual_center_y + spacing
        self.traffic_lights["east"].x = actual_center_x + spacing
        self.traffic_lights["east"].y = actual_center_y
        self.traffic_lights["west"].x = actual_center_x - spacing
        self.traffic_lights["west"].y = actual_center_y
        
        self.vip_flash_timer += 1
        
        for direction, light in self.traffic_lights.items():
            signal_map = {"north": 1, "east": 2, "south": 3, "west": 4}
            signal_num = signal_map.get(direction, 0)
            is_vip_signal = (self.vip_active and self.vip_signal_id == signal_num)
            
            # Draw VIP indicator with neon glow effect
            if is_vip_signal:
                flash_on = (self.vip_flash_timer // 5) % 2
                if flash_on:
                    # Outer glow
                    for i in range(10, 0, -1):
                        alpha = int(30 * (i / 10))
                        painter.setBrush(QBrush(QColor(255, 0, 100, alpha)))
                        painter.setPen(QPen(QColor(255, 0, 100, alpha), 2))
                        painter.drawRoundedRect(light.x - 60 - i, light.y - 140 - i, 
                                              120 + 2*i, 150 + 2*i, 15, 15)
                    
                    # VIP text with glow
                    painter.setPen(QPen(QColor(255, 255, 255), 3))
                    painter.setFont(QFont("Arial", 16, QFont.Bold))
                    painter.drawText(light.x - 35, light.y - 150, "VIP PRIORITY")
            
            # Draw traffic light pole with metallic gradient
            pole_gradient = QLinearGradient(light.x - 6, 0, light.x + 6, 0)
            pole_gradient.setColorAt(0, QColor(120, 120, 140))
            pole_gradient.setColorAt(0.5, QColor(80, 80, 100))
            pole_gradient.setColorAt(1, QColor(60, 60, 80))
            painter.setBrush(QBrush(pole_gradient))
            painter.setPen(QPen(QColor(40, 40, 60), 2))
            painter.drawRoundedRect(light.x - 8, light.y - 130, 16, 130, 8, 8)
            
            # Draw traffic light housing with glass effect
            housing_gradient = QLinearGradient(light.x - 50, light.y - 130, light.x + 50, light.y + 10)
            if is_vip_signal:
                housing_gradient.setColorAt(0, QColor(80, 40, 60, 180))
                housing_gradient.setColorAt(1, QColor(40, 20, 30, 220))
            else:
                housing_gradient.setColorAt(0, QColor(60, 60, 80, 180))
                housing_gradient.setColorAt(1, QColor(30, 30, 40, 220))
            
            painter.setBrush(QBrush(housing_gradient))
            painter.setPen(QPen(QColor(100, 100, 120, 150), 2))
            painter.drawRoundedRect(light.x - 50, light.y - 130, 100, 140, 20, 20)
            
            # Inner glass reflection
            reflection = QLinearGradient(light.x - 45, light.y - 125, light.x - 10, light.y - 90)
            reflection.setColorAt(0, QColor(255, 255, 255, 40))
            reflection.setColorAt(1, QColor(255, 255, 255, 5))
            painter.setBrush(QBrush(reflection))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(light.x - 45, light.y - 125, 35, 60, 15, 15)
            
            # Draw LED-style lights with glow effects
            self.draw_led_light(painter, light.x, light.y - 110, 32, light.red, QColor(255, 80, 80), "red")
            self.draw_led_light(painter, light.x, light.y - 65, 32, light.yellow, QColor(255, 255, 80), "yellow")
            self.draw_led_light(painter, light.x, light.y - 20, 32, light.green, QColor(80, 255, 80), "green", is_vip_signal)
            
            # Draw pedestrian signal with modern styling
            ped_x = light.x + (120 if direction in ["north", "south"] else 150)
            ped_y = light.y - 50 if direction in ["north", "south"] else light.y + 20
            
            # Pedestrian housing
            ped_gradient = QLinearGradient(ped_x - 25, ped_y - 45, ped_x + 25, ped_y + 15)
            if self.vip_active and not is_vip_signal:
                ped_gradient.setColorAt(0, QColor(80, 30, 30, 180))
                ped_gradient.setColorAt(1, QColor(40, 15, 15, 220))
            else:
                ped_gradient.setColorAt(0, QColor(50, 50, 70, 180))
                ped_gradient.setColorAt(1, QColor(25, 25, 35, 220))
            
            painter.setBrush(QBrush(ped_gradient))
            painter.setPen(QPen(QColor(80, 80, 100, 150), 2))
            painter.drawRoundedRect(ped_x - 25, ped_y - 45, 50, 60, 15, 15)
            
            # Pedestrian light
            if self.vip_active and not is_vip_signal:
                self.draw_led_light(painter, ped_x, ped_y - 15, 28, True, QColor(255, 80, 80), "red")
            elif light.pedestrian_green:
                self.draw_led_light(painter, ped_x, ped_y - 15, 28, True, QColor(80, 255, 80), "green")
            else:
                self.draw_led_light(painter, ped_x, ped_y - 15, 28, True, QColor(255, 80, 80), "red")
            
            # Modern labels with subtle glow
            painter.setPen(QPen(QColor(200, 200, 220), 2))
            painter.setFont(QFont("Arial", 11, QFont.Bold))
            painter.drawText(light.x - 35, light.y + 55, "TRAFFIC")
            painter.drawText(ped_x - 20, ped_y + 40, "WALK")
    
    def draw_led_light(self, painter, x, y, size, is_on, color, light_type, is_vip=False):
        """Draw LED-style light with glow effect"""
        radius = size // 2
        
        if is_on:
            # Outer glow effect
            glow_steps = 8
            for i in range(glow_steps, 0, -1):
                alpha = int(80 * (i / glow_steps) * (i / glow_steps))
                glow_color = QColor(color.red(), color.green(), color.blue(), alpha)
                painter.setBrush(QBrush(glow_color))
                painter.setPen(Qt.NoPen)
                glow_radius = radius + i * 3
                painter.drawEllipse(x - glow_radius, y - glow_radius, 
                                  glow_radius * 2, glow_radius * 2)
            
            # Main light with gradient
            light_gradient = QLinearGradient(x - radius, y - radius, x + radius, y + radius)
            if is_vip and light_type == "green":
                light_gradient.setColorAt(0, QColor(150, 255, 150))
                light_gradient.setColorAt(0.3, color)
                light_gradient.setColorAt(1, QColor(color.red()//2, color.green()//2, color.blue()//2))
            else:
                light_gradient.setColorAt(0, QColor(255, 255, 255, 100))
                light_gradient.setColorAt(0.3, color)
                light_gradient.setColorAt(1, QColor(color.red()//3, color.green()//3, color.blue()//3))
            
            painter.setBrush(QBrush(light_gradient))
            painter.setPen(QPen(QColor(color.red()//2, color.green()//2, color.blue()//2), 2))
        else:
            off_gradient = QLinearGradient(x - radius, y - radius, x + radius, y + radius)
            off_gradient.setColorAt(0, QColor(60, 60, 60))
            off_gradient.setColorAt(1, QColor(20, 20, 20))
            painter.setBrush(QBrush(off_gradient))
            painter.setPen(QPen(QColor(40, 40, 40), 1))
        
        painter.drawEllipse(x - radius, y - radius, size, size)
        
        # Add highlight reflection when on
        if is_on:
            highlight = QLinearGradient(x - radius//2, y - radius//2, x + radius//4, y + radius//4)
            highlight.setColorAt(0, QColor(255, 255, 255, 120))
            highlight.setColorAt(1, QColor(255, 255, 255, 0))
            painter.setBrush(QBrush(highlight))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(x - radius//2, y - radius//2, radius, radius)

class TrafficSystemUpdateThread(QThread):
    """Thread to handle server communication and updates"""
    
    status_updated = pyqtSignal(dict)
    countdown_updated = pyqtSignal(dict)
    connection_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.server = None
        self.running = False
        self.connect_to_server()
        
    def connect_to_server(self):
        """Connect to the traffic light server"""
        try:
            self.server = xmlrpc.client.ServerProxy("http://127.0.0.1:9000/", allow_none=True)
            _ = self.server.get_signal_status()
        except Exception as e:
            self.server = None
            self.connection_error.emit(f"Failed to connect to server: {str(e)}")
    
    def run(self):
        """Main thread loop to update traffic status"""
        self.running = True
        connection_retry_count = 0
        max_retry_attempts = 3
        
        while self.running:
            if self.server:
                try:
                    status = self.server.get_signal_status()
                    countdown_info = self.server.get_countdown_info()
                    
                    self.status_updated.emit(status)
                    self.countdown_updated.emit(countdown_info)
                    connection_retry_count = 0
                except Exception as e:
                    connection_retry_count += 1
                    if connection_retry_count <= max_retry_attempts:
                        self.connection_error.emit(f"Server communication error: {str(e)} (Attempt {connection_retry_count}/{max_retry_attempts})")
                        self.connect_to_server()
                    else:
                        self.server = None
                        self.connection_error.emit("Server connection failed. Running in offline mode.")
            
            self.msleep(1000)
    
    def stop(self):
        """Stop the update thread"""
        self.running = False

class TrafficLightSimulationUI(QMainWindow):
    """Main UI with modern dark theme styling"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Traffic Control System - Modern Interface")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply modern dark theme
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2b2b52, stop:1 #1a1a2e);
            }
            QWidget {
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4a4a6a;
                border-radius: 12px;
                margin-top: 1ex;
                padding-top: 12px;
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #00d4ff;
                font-size: 14px;
            }
            QPushButton {
                border: 2px solid #4a9eff;
                border-radius: 8px;
                padding: 8px 16px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(74, 158, 255, 0.3), stop:1 rgba(74, 158, 255, 0.1));
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(74, 158, 255, 0.5), stop:1 rgba(74, 158, 255, 0.3));
                border-color: #66b3ff;
            }
            QPushButton:pressed {
                background: rgba(74, 158, 255, 0.6);
            }
            QLabel {
                color: #e0e0e0;
                font-size: 12px;
            }
            QTextEdit {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid #4a4a6a;
                border-radius: 8px;
                color: #00ff88;
                font-family: 'Courier New', monospace;
                padding: 8px;
            }
            QStatusBar {
                background: rgba(0, 0, 0, 0.2);
                border-top: 1px solid #4a4a6a;
                color: #b0b0b0;
            }
        """)
        
        # Server connection
        self.update_thread = TrafficSystemUpdateThread()
        self.update_thread.status_updated.connect(self.update_traffic_status)
        self.update_thread.countdown_updated.connect(self.update_countdown_info)
        self.update_thread.connection_error.connect(self.handle_connection_error)
        
        # Auto cycling
        self.auto_cycle_timer = QTimer()
        self.auto_cycle_timer.timeout.connect(self.cycle_traffic_lights)
        self.auto_cycle_timer.start(8000)
        self.current_light_index = 1
        
        # Setup UI
        self.setup_ui()
        self.setup_status_bar()
        
        # Start the update thread
        self.update_thread.start()
        
    def setup_ui(self):
        """Setup the main UI layout with modern styling"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Simulation widget
        self.simulation_widget = TrafficSimulationWidget()
        splitter.addWidget(self.simulation_widget)
        
        # Control panel
        control_panel = self.create_control_panel()
        splitter.addWidget(control_panel)
        
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        
    def create_control_panel(self):
        """Create modern control panel"""
        panel = QWidget()
        panel.setFixedWidth(350)
        layout = QVBoxLayout(panel)
        layout.setSpacing(16)
        
        # Connection Status with modern styling
        connection_group = QGroupBox("System Status")
        connection_layout = QVBoxLayout(connection_group)
        
        self.connection_status = QLabel("Initializing connection...")
        self.connection_status.setStyleSheet("""
            color: #ffa500; 
            font-weight: bold; 
            padding: 12px;
            background: rgba(255, 165, 0, 0.1);
            border-radius: 6px;
            border: 1px solid rgba(255, 165, 0, 0.3);
        """)
        connection_layout.addWidget(self.connection_status)
        layout.addWidget(connection_group)
        
        # VIP Emergency with neon styling
        vip_group = QGroupBox("Emergency Override")
        vip_layout = QVBoxLayout(vip_group)
        
        vip_button_layout = QHBoxLayout()
        
        self.vip_north_btn = QPushButton("NORTH")
        self.vip_north_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 68, 68, 0.8), stop:1 rgba(255, 68, 68, 0.4));
                border: 2px solid #ff4444;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background: rgba(255, 68, 68, 0.9);
                box-shadow: 0 0 20px rgba(255, 68, 68, 0.5);
            }
        """)
        self.vip_north_btn.clicked.connect(lambda: self.trigger_vip_signal(1))
        
        self.vip_east_btn = QPushButton("EAST")
        self.vip_east_btn.setStyleSheet(self.vip_north_btn.styleSheet())
        self.vip_east_btn.clicked.connect(lambda: self.trigger_vip_signal(2))
        
        vip_button_layout.addWidget(self.vip_north_btn)
        vip_button_layout.addWidget(self.vip_east_btn)
        
        vip_button_layout2 = QHBoxLayout()
        
        self.vip_south_btn = QPushButton("SOUTH")
        self.vip_south_btn.setStyleSheet(self.vip_north_btn.styleSheet())
        self.vip_south_btn.clicked.connect(lambda: self.trigger_vip_signal(3))
        
        self.vip_west_btn = QPushButton("WEST")
        self.vip_west_btn.setStyleSheet(self.vip_north_btn.styleSheet())
        self.vip_west_btn.clicked.connect(lambda: self.trigger_vip_signal(4))
        
        vip_button_layout2.addWidget(self.vip_south_btn)
        vip_button_layout2.addWidget(self.vip_west_btn)
        
        vip_layout.addLayout(vip_button_layout)
        vip_layout.addLayout(vip_button_layout2)
        
        self.vip_status = QLabel("Status: Normal Operation")
        self.vip_status.setStyleSheet("""
            font-weight: bold; 
            padding: 8px;
            background: rgba(0, 255, 136, 0.1);
            border-radius: 4px;
            border: 1px solid rgba(0, 255, 136, 0.3);
        """)
        vip_layout.addWidget(self.vip_status)
        
        layout.addWidget(vip_group)
        
        # Load Test with modern styling
        load_group = QGroupBox("Performance Testing")
        load_layout = QVBoxLayout(load_group)
        
        self.load_test_btn = QPushButton("Execute Load Test")
        self.load_test_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(68, 68, 255, 0.8), stop:1 rgba(68, 68, 255, 0.4));
                border: 2px solid #4444ff;
                color: white;
                font-weight: bold;
                padding: 12px;
            }
            QPushButton:hover {
                background: rgba(68, 68, 255, 0.9);
            }
        """)
        self.load_test_btn.clicked.connect(self.run_load_simulation)
        load_layout.addWidget(self.load_test_btn)
        
        self.load_status = QLabel("Ready for testing")
        self.load_status.setStyleSheet("font-size: 11px; padding: 6px; color: #b0b0b0;")
        load_layout.addWidget(self.load_status)
        
        layout.addWidget(load_group)
        
        # RTO Control with grid styling
        rto_group = QGroupBox("Manual Override Controls")
        rto_layout = QVBoxLayout(rto_group)
        
        rto_grid = QGridLayout()
        
        # Headers with modern styling
        header_style = """
            QLabel {
                color: #00d4ff;
                font-weight: bold;
                font-size: 13px;
                padding: 8px;
                background: rgba(0, 212, 255, 0.1);
                border-radius: 6px;
                border: 1px solid rgba(0, 212, 255, 0.3);
            }
        """
        
        direction_header = QLabel("Direction")
        direction_header.setStyleSheet(header_style)
        direction_header.setAlignment(Qt.AlignCenter)
        rto_grid.addWidget(direction_header, 0, 0)
        
        traffic_header = QLabel("Traffic Signal")
        traffic_header.setStyleSheet(header_style)
        traffic_header.setAlignment(Qt.AlignCenter)
        rto_grid.addWidget(traffic_header, 0, 1)
        
        ped_header = QLabel("Pedestrian")
        ped_header.setStyleSheet(header_style)
        ped_header.setAlignment(Qt.AlignCenter)
        rto_grid.addWidget(ped_header, 0, 2)
        
        # Direction rows with modern button styling
        directions = ["North", "East", "South", "West"]
        self.rto_traffic_buttons = {}
        self.rto_ped_buttons = {}
        
        for i, direction in enumerate(directions, 1):
            # Direction label with modern styling
            dir_label = QLabel(direction)
            dir_label.setAlignment(Qt.AlignCenter)
            dir_label.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    font-weight: bold;
                    padding: 8px;
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 6px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }
            """)
            rto_grid.addWidget(dir_label, i, 0)
            
            # Traffic signal button with modern green styling
            traffic_btn = QPushButton("GREEN")
            traffic_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(68, 255, 68, 0.8), stop:1 rgba(68, 255, 68, 0.4));
                    border: 2px solid #44ff44;
                    color: black;
                    font-weight: bold;
                    min-height: 30px;
                    border-radius: 8px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background: rgba(68, 255, 68, 0.9);
                    box-shadow: 0 0 15px rgba(68, 255, 68, 0.4);
                }
            """)
            traffic_btn.clicked.connect(lambda checked, d=direction.lower(), s=i: self.toggle_rto_traffic(d, s))
            self.rto_traffic_buttons[direction.lower()] = traffic_btn
            rto_grid.addWidget(traffic_btn, i, 1)
            
            # Pedestrian signal button with modern red styling
            ped_btn = QPushButton("STOP")
            ped_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 68, 68, 0.8), stop:1 rgba(255, 68, 68, 0.4));
                    border: 2px solid #ff4444;
                    color: white;
                    font-weight: bold;
                    min-height: 30px;
                    border-radius: 8px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background: rgba(255, 68, 68, 0.9);
                    box-shadow: 0 0 15px rgba(255, 68, 68, 0.4);
                }
            """)
            ped_btn.clicked.connect(lambda checked, d=direction.lower(), s=i: self.toggle_rto_pedestrian(d, s))
            self.rto_ped_buttons[direction.lower()] = ped_btn
            rto_grid.addWidget(ped_btn, i, 2)
        
        rto_layout.addLayout(rto_grid)
        
        # RTO status with modern indicator
        self.rto_status = QLabel("Auto Cycle: ACTIVE")
        self.rto_status.setStyleSheet("""
            color: #00ff88;
            font-weight: bold;
            padding: 10px;
            background: rgba(0, 255, 136, 0.1);
            border-radius: 6px;
            border: 1px solid rgba(0, 255, 136, 0.3);
        """)
        rto_layout.addWidget(self.rto_status)
        
        self.rto_recycle_btn = QPushButton("RESET TO AUTO MODE")
        self.rto_recycle_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 170, 0, 0.8), stop:1 rgba(255, 170, 0, 0.4));
                border: 2px solid #ffaa00;
                color: black;
                font-weight: bold;
                padding: 12px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: rgba(255, 170, 0, 0.9);
                box-shadow: 0 0 20px rgba(255, 170, 0, 0.4);
            }
        """)
        self.rto_recycle_btn.clicked.connect(self.rto_recycle)
        rto_layout.addWidget(self.rto_recycle_btn)
        
        layout.addWidget(rto_group)
        
        # Countdown Information with modern digital display
        countdown_group = QGroupBox("System Timing")
        countdown_layout = QVBoxLayout(countdown_group)
        
        self.countdown_display = QLabel("Synchronizing with server...")
        self.countdown_display.setStyleSheet("""
            QLabel {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                padding: 15px;
                background: rgba(0, 0, 0, 0.4);
                border: 1px solid #4a4a6a;
                border-radius: 8px;
                color: #00ff88;
                line-height: 1.4;
            }
        """)
        countdown_layout.addWidget(self.countdown_display)
        
        layout.addWidget(countdown_group)
        
        # Traffic Status Display with terminal styling
        status_group = QGroupBox("System Log")
        status_layout = QVBoxLayout(status_group)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(160)
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet("""
            QTextEdit { 
                font-family: 'Courier New', monospace; 
                font-size: 10px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 0, 0, 0.8), stop:1 rgba(0, 0, 0, 0.6));
                border: 2px solid #4a4a6a;
                border-radius: 8px;
                color: #00ff88;
                padding: 10px;
                selection-background-color: rgba(0, 255, 136, 0.3);
            }
            QScrollBar:vertical {
                background: rgba(0, 0, 0, 0.3);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(74, 158, 255, 0.6);
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(74, 158, 255, 0.8);
            }
        """)
        status_layout.addWidget(self.status_text)
        
        layout.addWidget(status_group)
        
        layout.addStretch()
        return panel
    
    def setup_status_bar(self):
        """Setup modern status bar"""
        self.statusBar().showMessage("Traffic Control System - Modern Interface Active")
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 0, 0, 0.4), stop:1 rgba(0, 0, 0, 0.2));
                border-top: 1px solid rgba(74, 158, 255, 0.5);
                color: #e0e0e0;
                padding: 4px;
            }
        """)
        
        # Add current time with modern styling
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            QLabel {
                color: #00d4ff;
                font-weight: bold;
                padding: 4px 12px;
                background: rgba(0, 212, 255, 0.1);
                border-radius: 4px;
                border: 1px solid rgba(0, 212, 255, 0.3);
            }
        """)
        self.statusBar().addPermanentWidget(self.time_label)
        
        # Timer to update time
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
        self.update_time()
    
    def cycle_traffic_lights(self):
        """Automatically cycle through traffic lights to keep simulation realistic"""
        pass
    
    def update_traffic_status(self, status):
        """Update traffic light states based on server status"""
        try:
            self.simulation_widget.update_traffic_lights(status)
            self.update_status_display(status)
            
            self.connection_status.setText("Connected & Synchronized")
            self.connection_status.setStyleSheet("""
                color: #00ff88; 
                font-weight: bold; 
                padding: 12px;
                background: rgba(0, 255, 136, 0.1);
                border-radius: 6px;
                border: 1px solid rgba(0, 255, 136, 0.3);
            """)
            
        except Exception as e:
            self.handle_connection_error(f"Status update error: {str(e)}")
    
    def update_countdown_info(self, countdown_info):
        """Update countdown information in simulation widget"""
        try:
            self.simulation_widget.update_countdown_info(countdown_info)
            
            countdown_text = f"Active Pair: {countdown_info.get('current_pair', 'Unknown')}\n"
            countdown_text += f"Next Cycle: {countdown_info.get('next_pair', 'Unknown')}\n"
            countdown_text += f"Time Remaining: {countdown_info.get('time_remaining', 0):.1f}s\n"
            countdown_text += f"Green Signals: {countdown_info.get('current_green_signals', [])}"
            
            self.countdown_display.setText(countdown_text)
            
        except Exception as e:
            print(f"Countdown update error: {e}")
    
    def handle_connection_error(self, error_msg):
        """Handle server connection errors and fall back to local simulation"""
        print(f"Connection error: {error_msg}")
        
        self.connection_status.setText("Offline Mode - Local Simulation")
        self.connection_status.setStyleSheet("""
            color: #ffa500; 
            font-weight: bold; 
            padding: 12px;
            background: rgba(255, 165, 0, 0.1);
            border-radius: 6px;
            border: 1px solid rgba(255, 165, 0, 0.3);
        """)
        
        if "offline mode" in error_msg.lower() or "failed" in error_msg.lower():
            local_status = {
                "t1": "red", "t2": "red", "t3": "red", "t4": "red",
                "p1": "green", "p2": "green", "p3": "green", "p4": "green"
            }
            local_status[f"t{self.current_light_index}"] = "green"
            local_status[f"p{self.current_light_index}"] = "red"
            
            self.simulation_widget.update_traffic_lights(local_status)
            self.update_status_display(local_status)
    
    def update_status_display(self, status):
        """Update the status display text with current traffic light states"""
        try:
            status_text = "=== TRAFFIC CONTROL STATUS ===\n"
            status_text += f"NORTH: {status.get('t1', 'RED').upper():>7}  |  "
            status_text += f"EAST: {status.get('t2', 'RED').upper():>7}\n"
            status_text += f"SOUTH: {status.get('t3', 'RED').upper():>7}  |  "
            status_text += f"WEST: {status.get('t4', 'RED').upper():>7}\n"
            
            status_text += "\n=== PEDESTRIAN CROSSINGS ===\n"
            status_text += f"NORTH: {status.get('p1', 'GREEN').upper():>6}  |  "
            status_text += f"EAST: {status.get('p2', 'GREEN').upper():>6}\n"
            status_text += f"SOUTH: {status.get('p3', 'GREEN').upper():>6}  |  "
            status_text += f"WEST: {status.get('p4', 'GREEN').upper():>6}"
            
            self.status_text.setText(status_text)
            
        except Exception as e:
            self.status_text.setText(f"ERROR: Status display failed - {str(e)}")
    
    def update_time(self):
        """Update the current time display"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(f"{current_time}")
    
    def trigger_vip_signal(self, signal_id):
        """Trigger VIP emergency signal"""
        try:
            print(f"VIP Emergency: Triggering signal {signal_id}")
            self.vip_status.setText(f"EMERGENCY ACTIVE: Signal {signal_id}")
            self.vip_status.setStyleSheet("""
                color: #ff4444;
                font-weight: bold;
                padding: 8px;
                background: rgba(255, 68, 68, 0.2);
                border-radius: 4px;
                border: 2px solid rgba(255, 68, 68, 0.5);
            """)
            
            self.simulation_widget.set_vip_active(signal_id)
            
            if hasattr(self, 'update_thread') and self.update_thread.server:
                success = self.update_thread.server.vip_signal_manipulator(signal_id)
                if success:
                    print(f"VIP signal {signal_id} activated successfully")
                    self.status_text.append(f"\n>>> EMERGENCY OVERRIDE: Signal {signal_id} prioritized")
                    QTimer.singleShot(10000, self.reset_vip_status)
                else:
                    print(f"VIP signal {signal_id} activation failed")
                    self.vip_status.setText("EMERGENCY FAILED")
                    self.simulation_widget.clear_vip_active()
            else:
                print("No server connection for VIP request")
                self.vip_status.setText("CONNECTION ERROR")
                self.simulation_widget.clear_vip_active()
                
        except Exception as e:
            print(f"VIP signal error: {e}")
            self.vip_status.setText("SYSTEM ERROR")
            self.simulation_widget.clear_vip_active()
    
    def reset_vip_status(self):
        """Reset VIP status display to normal"""
        self.vip_status.setText("Status: Normal Operation")
        self.vip_status.setStyleSheet("""
            font-weight: bold; 
            padding: 8px;
            background: rgba(0, 255, 136, 0.1);
            border-radius: 4px;
            border: 1px solid rgba(0, 255, 136, 0.3);
        """)
        self.simulation_widget.clear_vip_active()
    
    def run_load_simulation(self):
        """Run load balancer simulation with multiple concurrent requests"""
        try:
            print("Starting load balancer simulation...")
            self.load_status.setText("Executing performance test...")
            self.load_test_btn.setEnabled(False)
            
            import threading
            from concurrent.futures import ThreadPoolExecutor
            
            def load_test_worker():
                try:
                    print("Executing 15 simultaneous requests to test load balancing")
                    
                    def single_request(request_id):
                        try:
                            import xmlrpc.client
                            test_server = xmlrpc.client.ServerProxy("http://127.0.0.1:9000/", allow_none=True)
                            
                            status = test_server.get_signal_status()
                            stats = test_server.get_system_stats()
                            countdown = test_server.get_countdown_info()
                            
                            return f"Request {request_id}: Success"
                        except Exception as e:
                            return f"Request {request_id}: Failed - {str(e)}"
                    
                    with ThreadPoolExecutor(max_workers=15) as executor:
                        futures = [executor.submit(single_request, i) for i in range(1, 16)]
                        results = [future.result(timeout=30) for future in futures]
                    
                    successful = len([r for r in results if "Success" in r])
                    failed = len(results) - successful
                    
                    def update_ui():
                        self.load_status.setText(f"Test complete: {successful}/15 successful")
                        self.load_test_btn.setEnabled(True)
                        self.status_text.append(f"\n>>> LOAD TEST: {successful} success, {failed} failed")
                        QTimer.singleShot(5000, lambda: self.load_status.setText("Ready for testing"))
                    
                    QTimer.singleShot(0, update_ui)
                    
                except Exception as e:
                    print(f"Load test error: {e}")
                    def update_error():
                        self.load_status.setText("Test failed - check connection")
                        self.load_test_btn.setEnabled(True)
                    QTimer.singleShot(0, update_error)
            
            test_thread = threading.Thread(target=load_test_worker)
            test_thread.daemon = True
            test_thread.start()
            
        except Exception as e:
            print(f"Load simulation error: {e}")
            self.load_status.setText("Error occurred")
            self.load_test_btn.setEnabled(True)
    
    def toggle_rto_traffic(self, direction, signal_num):
        """Toggle traffic signal for RTO manual control"""
        try:
            if not self.simulation_widget.rto_mode:
                self.simulation_widget.set_rto_mode(True)
                self.rto_status.setText("Auto Cycle: DISABLED")
                self.rto_status.setStyleSheet("""
                    color: #ff4444;
                    font-weight: bold;
                    padding: 10px;
                    background: rgba(255, 68, 68, 0.1);
                    border-radius: 6px;
                    border: 1px solid rgba(255, 68, 68, 0.3);
                """)
            
            button = self.rto_traffic_buttons[direction]
            current_text = button.text()
            
            if current_text == "STOP":
                new_state = "green"
                button.setText("GREEN")
                button.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 rgba(68, 255, 68, 0.8), stop:1 rgba(68, 255, 68, 0.4));
                        border: 2px solid #44ff44;
                        color: black;
                        font-weight: bold;
                        min-height: 30px;
                        border-radius: 8px;
                        padding: 6px;
                    }
                    QPushButton:hover {
                        background: rgba(68, 255, 68, 0.9);
                        box-shadow: 0 0 15px rgba(68, 255, 68, 0.4);
                    }
                """)
            elif current_text == "GREEN":
                new_state = "yellow"
                button.setText("CAUTION")
                button.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 rgba(255, 255, 68, 0.8), stop:1 rgba(255, 255, 68, 0.4));
                        border: 2px solid #ffff44;
                        color: black;
                        font-weight: bold;
                        min-height: 30px;
                        border-radius: 8px;
                        padding: 6px;
                    }
                    QPushButton:hover {
                        background: rgba(255, 255, 68, 0.9);
                        box-shadow: 0 0 15px rgba(255, 255, 68, 0.4);
                    }
                """)
            else:
                new_state = "red"
                button.setText("STOP")
                button.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 rgba(255, 68, 68, 0.8), stop:1 rgba(255, 68, 68, 0.4));
                        border: 2px solid #ff4444;
                        color: white;
                        font-weight: bold;
                        min-height: 30px;
                        border-radius: 8px;
                        padding: 6px;
                    }
                    QPushButton:hover {
                        background: rgba(255, 68, 68, 0.9);
                        box-shadow: 0 0 15px rgba(255, 68, 68, 0.4);
                    }
                """)
            
            self.simulation_widget.set_manual_signal_state(direction, "traffic", new_state)
            print(f"RTO: {direction.title()} traffic signal set to {new_state}")
            
        except Exception as e:
            print(f"RTO traffic toggle error: {e}")
    
    def toggle_rto_pedestrian(self, direction, signal_num):
        """Toggle pedestrian signal for RTO manual control"""
        try:
            if not self.simulation_widget.rto_mode:
                self.simulation_widget.set_rto_mode(True)
                self.rto_status.setText("Auto Cycle: DISABLED")
                self.rto_status.setStyleSheet("""
                    color: #ff4444;
                    font-weight: bold;
                    padding: 10px;
                    background: rgba(255, 68, 68, 0.1);
                    border-radius: 6px;
                    border: 1px solid rgba(255, 68, 68, 0.3);
                """)
            
            button = self.rto_ped_buttons[direction]
            current_text = button.text()
            
            if current_text == "STOP":
                new_state = "green"
                button.setText("WALK")
                button.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 rgba(68, 255, 68, 0.8), stop:1 rgba(68, 255, 68, 0.4));
                        border: 2px solid #44ff44;
                        color: black;
                        font-weight: bold;
                        min-height: 30px;
                        border-radius: 8px;
                        padding: 6px;
                    }
                    QPushButton:hover {
                        background: rgba(68, 255, 68, 0.9);
                        box-shadow: 0 0 15px rgba(68, 255, 68, 0.4);
                    }
                """)
            else:
                new_state = "red"
                button.setText("STOP")
                button.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 rgba(255, 68, 68, 0.8), stop:1 rgba(255, 68, 68, 0.4));
                        border: 2px solid #ff4444;
                        color: white;
                        font-weight: bold;
                        min-height: 30px;
                        border-radius: 8px;
                        padding: 6px;
                    }
                    QPushButton:hover {
                        background: rgba(255, 68, 68, 0.9);
                        box-shadow: 0 0 15px rgba(255, 68, 68, 0.4);
                    }
                """)
            
            self.simulation_widget.set_manual_signal_state(direction, "pedestrian", new_state)
            print(f"RTO: {direction.title()} pedestrian signal set to {new_state}")
            
        except Exception as e:
            print(f"RTO pedestrian toggle error: {e}")
    
    def rto_recycle(self):
        """Reset to initial state and restart auto-cycle"""
        try:
            print("RTO: Recycling to initial state...")
            
            self.simulation_widget.set_rto_mode(False)
            
            # Reset buttons with modern styling
            green_style = """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(68, 255, 68, 0.8), stop:1 rgba(68, 255, 68, 0.4));
                    border: 2px solid #44ff44;
                    color: black;
                    font-weight: bold;
                    min-height: 30px;
                    border-radius: 8px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background: rgba(68, 255, 68, 0.9);
                    box-shadow: 0 0 15px rgba(68, 255, 68, 0.4);
                }
            """
            
            red_style = """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 68, 68, 0.8), stop:1 rgba(255, 68, 68, 0.4));
                    border: 2px solid #ff4444;
                    color: white;
                    font-weight: bold;
                    min-height: 30px;
                    border-radius: 8px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background: rgba(255, 68, 68, 0.9);
                    box-shadow: 0 0 15px rgba(255, 68, 68, 0.4);
                }
            """
            
            # Reset to initial state
            self.rto_traffic_buttons["north"].setText("GREEN")
            self.rto_traffic_buttons["north"].setStyleSheet(green_style)
            self.rto_traffic_buttons["south"].setText("GREEN")
            self.rto_traffic_buttons["south"].setStyleSheet(green_style)
            self.rto_traffic_buttons["east"].setText("STOP")
            self.rto_traffic_buttons["east"].setStyleSheet(red_style)
            self.rto_traffic_buttons["west"].setText("STOP")
            self.rto_traffic_buttons["west"].setStyleSheet(red_style)
            
            self.rto_ped_buttons["north"].setText("STOP")
            self.rto_ped_buttons["north"].setStyleSheet(red_style)
            self.rto_ped_buttons["south"].setText("STOP")
            self.rto_ped_buttons["south"].setStyleSheet(red_style)
            self.rto_ped_buttons["east"].setText("WALK")
            self.rto_ped_buttons["east"].setStyleSheet(green_style)
            self.rto_ped_buttons["west"].setText("WALK")
            self.rto_ped_buttons["west"].setStyleSheet(green_style)
            
            # Update simulation states
            self.simulation_widget.set_manual_signal_state("north", "traffic", "green")
            self.simulation_widget.set_manual_signal_state("south", "traffic", "green")
            self.simulation_widget.set_manual_signal_state("east", "traffic", "red")
            self.simulation_widget.set_manual_signal_state("west", "traffic", "red")
            self.simulation_widget.set_manual_signal_state("north", "pedestrian", "red")
            self.simulation_widget.set_manual_signal_state("south", "pedestrian", "red")
            self.simulation_widget.set_manual_signal_state("east", "pedestrian", "green")
            self.simulation_widget.set_manual_signal_state("west", "pedestrian", "green")
            
            # Update status
            self.rto_status.setText("Auto Cycle: ACTIVE")
            self.rto_status.setStyleSheet("""
                color: #00ff88;
                font-weight: bold;
                padding: 10px;
                background: rgba(0, 255, 136, 0.1);
                border-radius: 6px;
                border: 1px solid rgba(0, 255, 136, 0.3);
            """)
            
            print("RTO: System recycled to initial state - auto-cycle resumed")
            
        except Exception as e:
            print(f"RTO recycle error: {e}")
    
    def closeEvent(self, event):
        """Clean up when closing the application"""
        if hasattr(self, 'update_thread'):
            self.update_thread.stop()
            self.update_thread.wait()
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Traffic Control System - Modern Interface")
    app.setApplicationVersion("3.0")
    
    # Set modern application styling
    app.setStyle('Fusion')
    
    # Dark palette for modern look
    palette = app.palette()
    palette.setColor(palette.Window, QColor(42, 42, 82))
    palette.setColor(palette.WindowText, QColor(255, 255, 255))
    palette.setColor(palette.Base, QColor(26, 26, 46))
    palette.setColor(palette.AlternateBase, QColor(66, 66, 66))
    palette.setColor(palette.ToolTipBase, QColor(0, 0, 0))
    palette.setColor(palette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(palette.Text, QColor(255, 255, 255))
    palette.setColor(palette.Button, QColor(53, 53, 53))
    palette.setColor(palette.ButtonText, QColor(255, 255, 255))
    palette.setColor(palette.BrightText, QColor(255, 0, 0))
    palette.setColor(palette.Link, QColor(42, 130, 218))
    palette.setColor(palette.Highlight, QColor(42, 130, 218))
    palette.setColor(palette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)
    
    # Create and show main window
    window = TrafficLightSimulationUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()