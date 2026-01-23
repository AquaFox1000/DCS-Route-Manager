
import asyncio
import websockets
import json
import threading
import logging
import socket
import time

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

    def start_daemon(self):
        """ Starts the Asyncio Loop in a separate Daemon Thread """
        if self.thread and self.thread.is_alive(): return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("📡 NetworkManager Daemon Started")

    def _run_loop(self):
        """ maintain a dedicated asyncio loop """
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()

    # --- HOST LOGIC ---
    def start_host(self, port, username):
        if self.mode != "IDLE": return False, "Already Active"
        self.port = port
        self.username = username
        self.mode = "HOST"
        asyncio.run_coroutine_threadsafe(self._start_host_server(), self.loop)
        return True, "Host Starting..."

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
        # New Client Connected
        self.connected_clients.add(websocket)
        logger.info(f"New Client: {websocket.remote_address}")
        self._emit_status("CLIENT_JOINED", {"count": len(self.connected_clients)})
        
        # Send current shared state to new client
        await self._sync_state_to_client(websocket)

        try:
            async for message in websocket:
                await self._process_message(message, websocket)
        except websockets.ConnectionClosed:
           pass
        finally:
            self.connected_clients.remove(websocket)
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
    def connect_to_host(self, ip, port, username):
        if self.mode != "IDLE": return False, "Already Active"
        self.target_ip = ip
        self.port = port
        self.username = username 
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
                
                # Send Handshake / Identify
                await websocket.send(json.dumps({"type": "identify", "username": self.username}))

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
        elif self.mode == "CLIENT" and self.client_connection:
             asyncio.run_coroutine_threadsafe(self.client_connection.close(), self.loop)
        
        self.mode = "IDLE"
        self.temp_shared_data = { "routes": [], "pois": [], "mission": {} }
        self._emit_status("STOPPED", {})
        return True, "Stopped"

    # --- MESSAGING & LOGIC ---
    async def _process_message(self, raw_msg, sender_socket):
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
        # Add 'origin' if missing? usually incoming has it.
        # Store in Temp
        category = "routes" if msg["type"] == "share_route" else "pois"
        item = msg.get("data")
        
        # Check if exists, update or append
        existing = next((x for x in self.temp_shared_data[category] if x.get("id") == item.get("id")), None)
        if existing:
            existing.update(item)
        else:
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
            "clients": list(self.client_map.values()) if self.mode == "HOST" else []
        }
