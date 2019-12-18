import socket
from dnslib import server

class TCPServerIPv6(server.TCPServer):
    address_family = socket.AF_INET6
class UDPServerIPv6(server.UDPServer):
    address_family = socket.AF_INET6
