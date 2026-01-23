import socket
import sys

print("--- DEBUG IP ---")
try:
    hostname = socket.gethostname()
    print(f"Hostname: {hostname}")
    print(f"gethostbyname: {socket.gethostbyname(hostname)}")
    
    try:
        name, aliases, ips = socket.gethostbyname_ex(hostname)
        print(f"gethostbyname_ex IPs: {ips}")
    except Exception as e:
        print(f"gethostbyname_ex error: {e}")

    print("\n--- SOCKET CONNECT TEST 8.8.8.8 ---")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        print(f"Socket Name: {s.getsockname()}")
        s.close()
    except Exception as e:
        print(f"Socket Connect Error: {e}")

except Exception as e:
    print(f"General Error: {e}")
print("----------------")
