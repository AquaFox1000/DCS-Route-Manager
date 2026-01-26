
import asyncio
import websockets
import json
import threading
import logging
import socket
import time
import upnpy
import requests

# Configure Logging
logger = logging.getLogger("NetworkManager")
logger.setLevel(logging.INFO)
current_user = "Unknown"

class NetworkManager:
    def __init__(self, flask_socketio=None, saved_routes_file=None, saved_pois_file=None):
        self.flask_socketio = flask_socketio
        self.loop = None
        self.thread = None
        self.mode = "IDLE" # IDLE, HOST, CLIENT
        self.running = False
        
        self.host_server = None
        self.client_connection = None
        self.connected_clients = set() # For Host
        self.client_map = {} # WebSocket -> Username

        
        # Temporary Data Storage (cleared on restart)
        self.temp_shared_data = {
            "routes": [],
            "pois": [],
            "mission": {} 
        }
        
        self.saved_routes_file = saved_routes_file
        self.saved_pois_file = saved_pois_file

        # Settings
        self.ip = "0.0.0.0"
        self.port = 5001
        self.username = "Player"
        self.target_ip = "127.0.0.1"

        # UPnP State
        self.use_upnp = False
        self.upnp_service = None
        self.public_ip = None
        self.password = None
        self.client_msg_rates = {}


    def start_daemon(self):
        """ Starts the Asyncio Loop in a separate Daemon Thread """
        if self.thread and self.thread.is_alive(): return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("NetworkManager Daemon Started")

    def _run_loop(self):
        """ maintain a dedicated asyncio loop """
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()

    # --- HOST LOGIC ---
    def start_host(self, port, username, password=None, use_upnp=False):
        if self.mode != "IDLE": return False, "Already Active"
        self.port = port
        self.username = username
        self.password = password
        self.mode = "HOST"
        self.use_upnp = use_upnp
        
        # Helper string for status
        upnp_msg = ""

        if self.use_upnp:
            logger.info("Attempting UPnP Discovery...")
            if self._setup_upnp(port):
                upnp_msg = " (UPnP Active)"
            else:
                upnp_msg = " (UPnP Failed)"
        
        # Always attempt to look up public IP if not found via UPnP
        if not self.public_ip:
             self.public_ip = self._get_external_ip()
             if self.public_ip: logger.info(f"Public IP (Fallback): {self.public_ip}")

        asyncio.run_coroutine_threadsafe(self._start_host_server(), self.loop)
        return True, f"Host Starting...{upnp_msg}"

    async def _start_host_server(self):
        logger.info(f"Hosting on Port {self.port}...")
        try:
            # Bind to all interfaces
            self.host_server = await websockets.serve(self._handle_client, "0.0.0.0", self.port)
            self._emit_status("HOST_ACTIVE", {"port": self.port, "users": 0})
        except Exception as e:
            logger.error(f"Host Fail: {e}")
            self.mode = "IDLE"
            self._emit_status("ERROR", {"msg": str(e)})

    async def _handle_client(self, websocket): 
        # New Client Connected - WAIT FOR AUTH
        logger.info(f"New Connection: {websocket.remote_address}")
        
        authenticated = False
        try:
            # Wait for Identification and Password
            auth_msg_raw = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            auth_msg = json.loads(auth_msg_raw)
            
            if auth_msg.get("type") == "identify":
                client_pass = auth_msg.get("password")
                username = auth_msg.get("username", "Unknown")
                
                # PASSWORD CHECK
                if self.password and client_pass != self.password:
                    logger.warning(f"Authentication Failed for {username}")
                    await websocket.send(json.dumps({"type": "error", "msg": "Invalid Password"}))
                    await websocket.close()
                    return

                # Auth Success
                authenticated = True
                self.connected_clients.add(websocket)
                self.client_map[websocket] = username
                logger.info(f"Client Authenticated: {username}")
                self._emit_status("CLIENT_JOINED", {"count": len(self.connected_clients)})
                
                # Send current shared state
                await self._sync_state_to_client(websocket)
            else:
                await websocket.close()
                return

            async for message in websocket:
                await self._process_message(message, websocket)
                
        except (asyncio.TimeoutError, websockets.ConnectionClosed, json.JSONDecodeError):
            pass
        finally:
            if authenticated:
                self.connected_clients.discard(websocket)
                if websocket in self.client_map: del self.client_map[websocket]
                logger.info("Client Disconnected")
                self._emit_status("CLIENT_LEFT", {"count": len(self.connected_clients)})

    async def _sync_state_to_client(self, websocket):
        """ Send all currently valid temp data to new joiner """
        if self.temp_shared_data["routes"]:
             msg = {"type": "bulk_sync", "category": "routes", "data": self.temp_shared_data["routes"]}
             await websocket.send(json.dumps(msg))
        if self.temp_shared_data["pois"]:
             msg = {"type": "bulk_sync", "category": "pois", "data": self.temp_shared_data["pois"]}
             await websocket.send(json.dumps(msg))

    # --- CLIENT LOGIC ---
    def connect_to_host(self, ip, port, username, password=None):
        if self.mode != "IDLE": return False, "Already Active"
        self.target_ip = ip
        self.port = port
        self.username = username 
        self.password = password
        self.mode = "CLIENT"
        asyncio.run_coroutine_threadsafe(self._connect_client(), self.loop)
        return True, "Connecting..."

    async def _connect_client(self):
        uri = f"ws://{self.target_ip}:{self.port}"
        logger.info(f"Connecting to {uri}...")
        try:
            async with websockets.connect(uri) as websocket:
                self.client_connection = websocket
                self._emit_status("CONNECTED", {"host": self.target_ip})
                
                # Send Handshake / Identify with Password
                await websocket.send(json.dumps({
                    "type": "identify", 
                    "username": self.username,
                    "password": self.password 
                }))

                async for message in websocket:
                    await self._process_message(message, websocket)
        except Exception as e:
             logger.error(f"Connection Failed: {e}")
             self.mode = "IDLE"
             self._emit_status("ERROR", {"msg": str(e)})

    def stop(self):
        """ Stop Host or Client """
        if self.mode == "HOST" and self.host_server:
            self.host_server.close()
            asyncio.run_coroutine_threadsafe(self.host_server.wait_closed(), self.loop)
            if self.use_upnp:
                self._teardown_upnp()
        elif self.mode == "CLIENT" and self.client_connection:
             asyncio.run_coroutine_threadsafe(self.client_connection.close(), self.loop)
        
        self.mode = "IDLE"
        self.temp_shared_data = { "routes": [], "pois": [], "mission": {} }
        self.use_upnp = False
        self._emit_status("STOPPED", {})
        return True, "Stopped"

    # --- UPNP HELPERS ---
    def _setup_upnp(self, port):
        try:
            upnp = upnpy.UPnP()
            devices = upnp.discover()
            
            # Find an IGD (Internet Gateway Device)
            if devices:
                device = upnp.get_igd()
                
                # Get the service that manages WAN connections
                # Usually WANIPConnection.1 or WANPPPConnection.1
                for service in device.services:
                    if "WANIPConnection" in service.service_type or "WANPPPConnection" in service.service_type:
                        self.upnp_service = service
                        break
                
                if self.upnp_service:
                    # Get External IP
                    # Actions often named 'GetExternalIPAddress'
                    try:
                        actions = self.upnp_service.get_actions()
                        if 'GetExternalIPAddress' in actions:
                            ip_response = self.upnp_service.GetExternalIPAddress()
                            self.public_ip = ip_response.get('NewExternalIPAddress')
                            logger.info(f"Public IP found: {self.public_ip}")
                    except:
                        logger.warning("UPnP: Could not fetch External IP")

                    # Add Port Mapping
                    # AddPortMapping(NewRemoteHost, NewExternalPort, NewProtocol, NewInternalPort, NewInternalClient, NewEnabled, NewPortMappingDescription, NewLeaseDuration)
                    self.upnp_service.AddPortMapping(
                        NewRemoteHost='',
                        NewExternalPort=port,
                        NewProtocol='TCP',
                        NewInternalPort=port,
                        NewInternalClient=self._get_local_ip(),
                        NewEnabled=1,
                        NewPortMappingDescription='DCS Route Manager',
                        NewLeaseDuration=0
                    )
                    logger.info(f"UPnP Port Mapping Added: {port} (TCP) -> Local")
                    return True
            
            logger.warning("UPnP: No compatible IGD found.")
            return False

        except Exception as e:
            logger.error(f"UPnP Setup Failed: {e}")
            return False

    def _teardown_upnp(self):
        if not self.upnp_service: return
        try:
            logger.info(f"Removing UPnP Mapping for Port {self.port}...")
            self.upnp_service.DeletePortMapping(
                NewRemoteHost='',
                NewExternalPort=self.port,
                NewProtocol='TCP'
            )
            self.upnp_service = None
            self.public_ip = None
        except Exception as e:
            logger.error(f"UPnP Teardown Error: {e}")

    def _get_local_ip(self):
        """ Best guess local network IP """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def _get_external_ip(self):
        """ Fetch external IP via fallback service """
        try:
            return requests.get('https://api.ipify.org', timeout=3).text
        except:
            return None

    # --- MESSAGING & LOGIC ---
    async def _process_message(self, raw_msg, sender_socket):
        # FLOOD CONTROL (HOST ONLY)
        if self.mode == "HOST":
            now = time.time()
            if sender_socket not in self.client_msg_rates:
                self.client_msg_rates[sender_socket] = {"count": 0, "start": now}
            
            rate = self.client_msg_rates[sender_socket]
            if now - rate["start"] > 1.0:
                rate["count"] = 0
                rate["start"] = now
            
            rate["count"] += 1
            if rate["count"] > 20: # 20 msgs per second limit (generous)
                if rate["count"] == 21: logger.warning(f"Flood limit hit for {self.client_map.get(sender_socket)}")
                return 

        try:
            msg = json.loads(raw_msg)
            mtype = msg.get("type")
            
            # BROADCASTING LOGIC (Host only)
            # If we are Host, we must relay this message to all OTHER clients
            if self.mode == "HOST":
                await self._broadcast(raw_msg, exclude=sender_socket)

            # HANDLING LOGIC
            if mtype == "identify":
                username = msg.get('username', 'Unknown')
                logger.info(f"User Identified: {username}")
                self.client_map[sender_socket] = username

            elif mtype in ["share_route", "share_poi", "share_mission"]:
                self._handle_shared_data(msg)

            elif mtype == "bulk_sync":
                 # Receive bulk data (Client receiving from Host)
                 cat = msg.get("category")
                 if cat == "routes": self.temp_shared_data["routes"] = msg.get("data")
                 elif cat == "pois": self.temp_shared_data["pois"] = msg.get("data")
                 # Notify Frontend
                 if self.flask_socketio:
                     self.flask_socketio.emit('mp_bulk_sync', msg)

        except Exception as e:
            logger.error(f"Msg Error: {e}")

    async def _broadcast(self, raw_msg, exclude=None):
        if self.mode != "HOST": return
        tasks = []
        for client in self.connected_clients:
            if client != exclude:
                tasks.append(client.send(raw_msg))
        if tasks: await asyncio.gather(*tasks, return_exceptions=True)

    def _handle_shared_data(self, msg):
        """ valid data received from network """
        # Store in Temp
        category = "routes" if msg["type"] == "share_route" else "pois"
        item = msg.get("data")
        sender = msg.get("origin", "Unknown")
        
        # Check if exists, update or append
        existing_idx = next((i for i, x in enumerate(self.temp_shared_data[category]) if x.get("id") == item.get("id")), -1)
        
        if existing_idx != -1:
            existing = self.temp_shared_data[category][existing_idx]
            
            # OWNERSHIP / CO-OP Logic
            # Shared = Read Only (unless Owner)
            # Co-op = Collaborative (Anyone can edit)
            
            owner = existing.get("owner", sender)
            is_coop = existing.get("coop", False) or item.get("coop", False)
            
            # If not owner and not co-op, reject modification
            if owner != sender and not is_coop:
                logger.warning(f"REJECTED: Update to {item.get('name')} by {sender} (Owner: {owner})")
                return 

            self.temp_shared_data[category][existing_idx].update(item)
            # Persist Owner
            self.temp_shared_data[category][existing_idx]["owner"] = owner
        else:
            # New Item - Set Owner
            item["owner"] = sender
            self.temp_shared_data[category].append(item)
            
        # Emit to Flask Logic (to update Map)
        if self.flask_socketio:
            self.flask_socketio.emit('mp_data_update', msg)

    # --- PUBLIC API FOR SERVER.PY ---
    def send_share_item(self, mtype, data):
        """ Call from Flask to send data out """
        if self.mode == "IDLE": return False
        
        payload = {
            "type": mtype, # share_route / share_poi
            "data": data,
            "origin": self.username
        }
        json_payload = json.dumps(payload)
        
        # If Host, update self and broadcast
        if self.mode == "HOST":
            self._handle_shared_data(payload) # Update local temp/UI
            asyncio.run_coroutine_threadsafe(self._broadcast(json_payload), self.loop)
        
        # If Client, send to Host
        elif self.mode == "CLIENT" and self.client_connection:
             asyncio.run_coroutine_threadsafe(self.client_connection.send(json_payload), self.loop)
             # Update local temp/UI immediately too? Yes, for feedback.
             self._handle_shared_data(payload) 

        return True

    def _emit_status(self, status, details):
        if self.flask_socketio:
            self.flask_socketio.emit('mp_status', {"status": status, "details": details})

    def get_status(self):
        return {
            "mode": self.mode,
            "ip": self.ip, # Host IP or Target IP
            "port": self.port,
            "username": self.username,
            "users": len(self.connected_clients) if self.mode == "HOST" else 0,
            "clients": list(self.client_map.values()) if self.mode == "HOST" else [],
            "upnp": self.use_upnp,
            "public_ip": self.public_ip,
            "upnp_status": "Active" if self.use_upnp and self.upnp_service else "Disabled"
        }
