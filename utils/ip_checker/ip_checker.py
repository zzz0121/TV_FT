import socket
from urllib.parse import urlparse

from qqwry import QQwry


class IPChecker:
    def __init__(self):
        self.q = QQwry()
        self.q.load_file("utils/ip_checker/data/qqwry.dat")
        self.url_host = {}
        self.host_ip = {}
        self.host_ipv_type = {}

    def get_host(self, url: str) -> str:
        """
        Get the host from a URL
        """
        if url in self.url_host:
            return self.url_host[url]

        host = urlparse(url).hostname or url
        self.url_host[url] = host
        return host

    def get_ip(self, url: str) -> str | None:
        """
        Get the IP from a URL
        """
        host = self.get_host(url)
        if host in self.host_ip:
            return self.host_ip[host]

        try:
            ip = socket.gethostbyname(host)
        except socket.gaierror:
            ip = None

        self.host_ip[host] = ip
        return ip

    def get_ipv_type(self, url: str) -> str:
        """
        Get the IPv type of URL
        """
        host = self.get_host(url)
        if host in self.host_ipv_type:
            return self.host_ipv_type[host]

        try:
            addr_info = socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            ipv_type = "ipv6" if any(info[0] == socket.AF_INET6 for info in addr_info) else "ipv4"
        except socket.gaierror:
            ipv_type = "ipv4"

        self.host_ipv_type[host] = ipv_type
        return ipv_type

    def lookup(self, ip: str) -> tuple[str | None, str | None]:
        """
        Lookup the IP address and return the country and organization
        :param ip: The IP address to lookup
        :return: A tuple of (country, organization)
        """
        try:
            result = self.q.lookup(ip)
            if result:
                return result[0], result[1]
            else:
                return None, None
        except Exception as e:
            print(f"Error on lookup: {e}")
            return None, None
