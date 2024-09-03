# encoding= utf-8
# __author__= gary
import cv2
import time
import os
from scapy.all import ARP, Ether, srp
import ipaddress

def scan_network(ip_range):
    arp = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether/arp
    result = srp(packet, timeout=3, verbose=0)[0]
    devices = []
    for sent, received in result:
        devices.append({'ip': received.psrc, 'mac': received.hwsrc})
    return devices

def get_local_ip_range():
    import socket
    ip = socket.gethostbyname(socket.gethostname())
    return f"{ip.rsplit('.', 1)[0]}.0/24"

# Scan for devices
ip_range = get_local_ip_range()
print(f"Scanning IP range: {ip_range}")
devices = scan_network(ip_range)

print("Devices found:")
for device in devices:
    print(f"IP: {device['ip']}\tMAC: {device['mac']}")