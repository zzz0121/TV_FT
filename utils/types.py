from typing import TypedDict, Literal

OriginType = Literal["local", "whitelist", "subscribe", "hotel", "multicast", "online_search"]
IPvType = Literal["ipv4", "ipv6"]


class ChannelData(TypedDict):
    """
    Channel data types, including url, date, resolution, origin and ipv_type
    """
    url: str
    date: str | None
    resolution: str | None
    origin: OriginType
