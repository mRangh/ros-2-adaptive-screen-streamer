from dataclasses import dataclass
from typing import Literal, Union, Optional
import re
import socket
import argparse

def get_sanitize_hostname():
    name = socket.gethostname()
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    if name and name[0].isdigit():
        name = "_" + name
    return name

@dataclass
class StreamConfig():
    target_frame_rate:float = 30
    monitor:int = 1
    quality:Union[int, Literal["auto"]] = "auto"

    min_jpeg_quality:int = 10
    max_jpeg_quality:int = 90
    start_jpeg_quality:int = 40

    show_incoming_stream:bool = True

    local_hostname:str = get_sanitize_hostname()
    target_hostname:Optional[str] = None
    target_ip:str = ""

    publish:bool = False

parser = argparse.ArgumentParser(description="ROS2 Screen Streamer Configuration")
parser.add_argument("--publish", action="store_true", help="Publish your screen")
parser.add_argument("--fps", type=float, help="Target frame rate (eg: 30, 60)")
parser.add_argument("--monitor", type=int, help="Source monitor index (eg: 0 - Mosaic, 1 - Main monitor)")
parser.add_argument("--quality", type=str, help="Pre-fixed quality (0-100%) or \"auto\"")
parser.add_argument("--headless", action="store_true", help="Hide visual interface")
parser.add_argument("--host", type=str, help="Target host name to subscribe to")
parser.add_argument("--ip", type=str, help="Target Tailscale IP for routing", default="")

args, _ = parser.parse_known_args()

if args.publish:
    StreamConfig.publish = True
if args.fps is not None:
    StreamConfig.target_frame_rate = args.fps
if args.monitor is not None:
    StreamConfig.monitor = args.monitor
if args.quality is not None:
    if args.quality.lower() == "auto":
        StreamConfig.quality = "auto"
    else:
        StreamConfig.quality = max(0, min(100, int(args.quality)))
if args.headless:
    StreamConfig.show_incoming_stream = False
if args.host is not None:
    clean_host = re.sub(r'[^a-zA-Z0-9_]', '_', args.host)
    if clean_host and clean_host[0].isdigit():
        clean_host = "pc_" + clean_host
    StreamConfig.target_hostname = clean_host
if args.ip:
    StreamConfig.target_ip = args.ip
