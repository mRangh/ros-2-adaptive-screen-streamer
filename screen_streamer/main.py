import os
import sys
import tempfile
from screen_streamer import StreamConfig

def setup_network() -> None:
    if not StreamConfig.target_ip:
        print("[WARN] No IP provided (--ip). Unicast discovery unable.")
        peers_xml = ''
    else:
        peers_xml = f'<Peer address="{StreamConfig.target_ip}"/>'

    xml_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
<CycloneDDS xmlns="https://cdds.io/config" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Domain id="any">
        <General>
            <Interfaces>
                <NetworkInterface name="tailscale0"/>
            </Interfaces>
            <AllowMulticast>false</AllowMulticast>
        </General>
        <Internal>
            <SocketReceiveBufferSize>10485760</SocketReceiveBufferSize>
        </Internal>
        <Discovery>
            <Peers>
                {peers_xml}
            </Peers>
            <ParticipantIndex>auto</ParticipantIndex>
        </Discovery>
    </Domain>
</CycloneDDS>"""

    xml_path = os.path.join(tempfile.gettempdir(), "cyclonedds.xml")
    with open(xml_path, "w") as f:
        f.write(xml_content)

    os.environ["RMW_IMPLEMENTATION"] = "rmw_cyclonedds_cpp"
    os.environ["CYCLONEDDS_URI"] = f"file://{xml_path}"
    os.environ["ROS_DOMAIN_ID"] = "42"

def main(args=None):
    if not StreamConfig.publish and not StreamConfig.target_hostname:
        print("Error: Provide --publish to broadcast, --host <target> to watch, or BOTH.")
        sys.exit(1)

    setup_network()

    import rclpy
    from rclpy.executors import MultiThreadedExecutor
    from screen_publisher import ScreenPublisher 
    from screen_subscriber import ScreenSubscriber

    rclpy.init(args=args)

    executor = MultiThreadedExecutor()
    nodes_to_spin = []

    if StreamConfig.publish:
        print(f"Starting PUBLISHER at namespace: /{StreamConfig.local_hostname}")
        pub_node = ScreenPublisher()
        nodes_to_spin.append(pub_node)
        executor.add_node(pub_node)

    if StreamConfig.target_hostname:
        print(f"Starting SUBSCRIBER connected to namespace: /{StreamConfig.target_hostname}")
        sub_node = ScreenSubscriber()
        nodes_to_spin.append(sub_node)
        executor.add_node(sub_node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        for node in nodes_to_spin:
            node.destroy_node()

        try:
            rclpy.shutdown()
        except Exception:
            pass

if __name__ == '__main__':
    main()
