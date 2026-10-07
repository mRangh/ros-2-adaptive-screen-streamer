import cv2
import mss
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import Float32, Header

from screen_streamer import StreamConfig

class ScreenPublisher(Node):
    def __init__(self) -> None:
        super().__init__("screen_publisher", namespace=StreamConfig.local_hostname)

        qos_profile = QoSProfile(
            reliability = QoSReliabilityPolicy.BEST_EFFORT,
            history = QoSHistoryPolicy.KEEP_LAST,
            depth = 1
        )

        self.publisher_ = self.create_publisher(CompressedImage, "screen_stream/compressed", qos_profile)
        self.feedback_sub = self.create_subscription(Float32, "stream_feedback", self.feedback_callback, 10)

        self.timer = self.create_timer(1/StreamConfig.target_frame_rate, self.timer_callback)
        self.sct = None
        self.monitor_idx = StreamConfig.monitor

        self.current_quality = StreamConfig.start_jpeg_quality if StreamConfig.quality == "auto" else StreamConfig.quality

        self.scale_factor = 1.0

    def feedback_callback(self, msg: Float32) -> None:
        if StreamConfig.quality != "auto":
            return

        received_fps = msg.data
        error_fps = StreamConfig.target_frame_rate - received_fps

        if error_fps > 5.0:
            if self.current_quality <= 30 and self.scale_factor == 1.0:
                self.scale_factor = 0.5
                self.get_logger().warn("Rede engarrafada! A reduzir resolução para 50%.")
            else:
                self.current_quality = max(StreamConfig.min_jpeg_quality, self.current_quality - 10)

        elif error_fps < 1.0:
            if self.scale_factor < 1.0 and self.current_quality >= 60:
                self.scale_factor = 1.0
                self.get_logger().info("Rede estabilizada. A restaurar resolução para 100%.")
            else:
                self.current_quality = min(StreamConfig.max_jpeg_quality, self.current_quality + 5)

        self.get_logger().info(f"Feedback: {received_fps:.1f} FPS | Qualidade: {self.current_quality}% | Escala: {self.scale_factor}x")

    def timer_callback(self):
        if self.sct is None:
            self.sct = mss.mss()
            self.monitor = self.sct.monitors[self.monitor_idx]

        sct_img = self.sct.grab(self.monitor)
        img = np.frombuffer(sct_img.bgra, dtype=np.uint8).reshape(sct_img.height, sct_img.width, 4)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        if self.scale_factor < 1.0:
            width = int(img.shape[1] * self.scale_factor)
            height = int(img.shape[0] * self.scale_factor)
            img = cv2.resize(img, (width, height), interpolation=cv2.INTER_LINEAR)

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.current_quality]
        success, encode_img = cv2.imencode(".jpg", img, encode_param)

        if success:
            msg = CompressedImage()

            hdr = Header()
            hdr.stamp = self.get_clock().now().to_msg()
            hdr.frame_id = "screen_link"

            msg.header = hdr
            msg.format = "jpeg"
            msg.data = encode_img.tobytes()
            self.publisher_.publish(msg)

    def destroy_node(self):
        if self.sct is not None:
            self.sct.close()
        super().destroy_node()

def main(args=None) -> None:
    rclpy.init(args=args)
    node = ScreenPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
