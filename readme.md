# Text-based-DNS (a.k.a. DNS53) to DNS-over-HTTPS Proxy
This project aims to apply DNS-over-HTTPS system-wide by setting up a local DNS server or by using mini PCs to act as a network gateway, that redirect requests to several DNS-over-HTTPS providers, thus effectively bypassing any Transparent DNS Proxy employed by ISP / Firewall.

## Installation
**Note: It is recommended to use & _activate_ any virtual environment module for Python before installing**
1. Install the required requirements listed in req.txt <pre>pip install -r req.txt</pre>
2. Run main.py with python <pre>python main.py</pre>
3. Set your DNS server in your connection to point to localhost (`127.0.0.1` for IPv4 or `::1` for IPv6)

