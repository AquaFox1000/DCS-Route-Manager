import socket
import threading
import time
import json

class DCSHookClient:
    """
    Handles the TCP connection to the DCS RouteManagerHook (Port 11002).
    Implements a robust state machine:
    - Boot Mode: Fast retries on startup.
    - Active Mode: Lazy reconnection (only when UDP is alive).
    - Failure Handling: 3-strike rule for zero-byte reads.
    """
    def __init__(self, port=11002, callback=None, udp_timeout=5.0):
        self.port = port
        self.callback_func = callback # Function to call with parsed data (usually socketio.emit)
        self.udp_timeout = udp_timeout
        
        self.tcp_socket = None
        self.udp_alive_flag = False
        self.last_udp_time = 0
        self.running = False
        self.thread = None

    def start(self):
        """ Starts the background connector thread """
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._connector_loop)
        self.thread.daemon = True
        self.thread.start()
        print(f"TCP Connector: Started (Port {self.port})")

    def stop(self):
        self.running = False
        if self.tcp_socket:
            try:
                self.tcp_socket.close()
            except:
                pass
        
    def set_udp_alive(self):
        """ Call this when UDP telemetry is received to wake up the TCP connector """
        self.udp_alive_flag = True
        self.last_udp_time = time.time()
        
    def send_packet(self, data):
        """ Sends a dictionary as a JSON line """
        if not self.tcp_socket: return False
        try:
            payload = json.dumps(data) + "\n"
            self.tcp_socket.sendall(payload.encode('utf-8'))
            return True
        except Exception as e:
            print(f"TCP Send Error: {e}")
            return False

    def _connector_loop(self):
        print("TCP Boot Mode: Attempting 3 initial connections...")
        # 1. BOOT MODE (Try to connect early)
        for i in range(3):
            if not self.running: return
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1.0)
                sock.connect(("127.0.0.1", self.port))
                sock.settimeout(None) 
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                
                print(f"Connected to DCS Hook (Boot Phase)")
                self.tcp_socket = sock
                self._read_loop(sock)
                break # If read loop returns, we disconnected
            except (ConnectionRefusedError, socket.timeout):
                print(f"   Boot Attempt {i+1}/3 failed")
                time.sleep(2.0)
            except Exception as e:
                print(f"   Boot Error: {e}")
                time.sleep(2.0)

        print("Entering Active Mode (Waiting for UDP Trigger)...")

        # 2. ACTIVE MODE
        while self.running:
            try:
                # Smart Reconnection: Only if UDP is flowing
                if not self.udp_alive_flag:
                    time.sleep(1.0)
                    continue
                    
                # UDP Stale Check
                if time.time() - self.last_udp_time > self.udp_timeout:
                    if self.udp_alive_flag:
                        print("UDP Flow Lost (Timeout 5s)")
                        self.udp_alive_flag = False
                    time.sleep(1.0)
                    continue
                    
                # Attempt Connection
                print("UDP Active - Connecting to Hook...")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2.0)
                
                try:
                    sock.connect(("127.0.0.1", self.port))
                    sock.settimeout(None)
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    
                    print(f"Connected to DCS Hook (Active Phase)")
                    self.tcp_socket = sock
                    self._read_loop(sock) # Block here until disconnect
                    
                except (ConnectionRefusedError, socket.timeout):
                    print("   Hook not listening... retrying in 1s")
                    time.sleep(1.0)
                    
            except Exception as e:
                print(f"TCP Connector Crash: {e}")
                time.sleep(5.0)

    def _read_loop(self, sock):
        buffer = ""
        zero_byte_strikes = 0
        
        try:
            while self.running:
                # Activity Check
                if time.time() - self.last_udp_time > self.udp_timeout:
                   print("Disconnect: Activity Timeout")
                   break
                   
                try:
                    data = sock.recv(4096)
                    
                    if not data:
                        zero_byte_strikes += 1
                        if zero_byte_strikes >= 3:
                            print("Disconnect: 3x Zero-Byte Reads")
                            break
                        time.sleep(0.1)
                        continue
                    else:
                        zero_byte_strikes = 0
                        self.last_udp_time = time.time() # Reset Watchdog
                        
                    buffer += data.decode('utf-8', errors='ignore')
                    
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if not line.strip(): continue
                        
                        try:
                            msg = json.loads(line)
                            self._handle_message(msg)
                        except:
                            pass
                            
                except ConnectionResetError:
                    print("Disconnect: Connection Reset")
                    break
                    
        except Exception as e:
            print(f"Disconnect Error: {e}")
            
        finally:
            try:
                sock.close()
            except:
                pass
            self.tcp_socket = None

    def _handle_message(self, msg):
        msg_type = msg.get("type")
        
        if msg_type == "heartbeat":
             pass
        elif msg_type == "metadata":
             data = msg.get("data", {})
             print(f"Metadata: Player={data.get('player_name')}, Unit={data.get('unit_name')}")
             if self.callback_func: self.callback_func('metadata', data)
             
        elif msg_type == "phonebook":
             data = msg.get("data", {})
             count = len(data) if data else 0
             print(f"Phonebook: {count} players")
             if self.callback_func: self.callback_func('phonebook', data)
             
        elif msg_type == "theater_state":
             data = msg.get("data", {})
             count = len(data) if data else 0
             print(f"Objects: {count}")
             if self.callback_func: self.callback_func('theater_state', data)
             
        elif msg_type == "config":
             # Echo back or handle config confirmations
             pass
