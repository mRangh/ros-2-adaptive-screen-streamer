import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import Float32, Header
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
import cv2
import numpy as np

from screen_streamer import StreamConfig

class ScreenSubscriber(Node):
    def __init__(self):
        super().__init__("screen_subscriber", namespace=StreamConfig.target_hostname)

        qos_profile = QoSProfile(
            reliability = QoSReliabilityPolicy.BEST_EFFORT,
            history = QoSHistoryPolicy.KEEP_LAST,
            depth = 1
        )

        self.subscription = self.create_subscription(
            CompressedImage, "screen_stream/compressed", self.listener_callback, qos_profile
        )

        self.feedback_pub = self.create_publisher(Float32, "stream_feedback", 10)

        self.received_frames = 0
        self.timer_fps = self.create_timer(1.0, self.calculate_and_publish_fps)

    def listener_callback(self, msg) -> None:
        self.received_frames += 1
        if StreamConfig.show_incoming_stream:
            np_arr = np.frombuffer(msg.data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if frame is None:
                return
            cv2.imshow("Remote Screen", frame)
            cv2.waitKey(1)

    def calculate_and_publish_fps(self):
        msg = Float32()
        msg.data = float(self.received_frames)
        self.feedback_pub.publish(msg)

        self.received_frames = 0

def main(args=None):
    rclpy.init(args=args)
    node = ScreenSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    cv2.destroyAllWindows()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
