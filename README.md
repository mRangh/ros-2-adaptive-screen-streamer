# screen_streamer

Screen streaming between machines using **ROS 2**, **CycloneDDS**, and **Tailscale**. One machine publishes its own screen as a `sensor_msgs/CompressedImage` (JPEG) and another subscribes and displays the video in real time. The JPEG quality is adjusted automatically based on the FPS the viewer is actually able to receive.

## How it works

```
 ┌────────────────────────┐   screen_stream/compressed    ┌────────────────────────┐
 │  Publisher             │ ────────────────────────────▶ │  Subscriber            │
 │  /<local_hostname>     │   (CompressedImage, JPEG,     │  /<target_hostname>    │
 │  mss → OpenCV → JPEG   │    BEST_EFFORT, depth 1)      │  imdecode → imshow     │
 │                        │ ◀──────────────────────────── │                        │
 └────────────────────────┘   stream_feedback (Float32)   └────────────────────────┘
                                   received FPS/s
```

- **Publisher**: captures the monitor with [`mss`](https://github.com/BoboTiG/python-mss), encodes it as JPEG with OpenCV, and publishes it on the topic `/<local_hostname>/screen_stream/compressed`.
- **Subscriber**: receives the frames, decodes them, and shows them in a window (or just counts them with `--headless`). Every second it publishes the number of frames received on `/<target_hostname>/stream_feedback`.
- **Auto quality**: in `auto` mode, the publisher compares the received FPS against the target FPS. If the error is greater than 5 FPS, quality drops by 10 points; if it is below 1 FPS, quality rises by 2 points, always within `[min_jpeg_quality, max_jpeg_quality]`.
- **Networking**: `main.py` generates a `cyclonedds.xml` that forces the `tailscale0` interface, disables multicast, and uses unicast discovery pointing at the IP given in `--ip`. It also sets `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` and `ROS_DOMAIN_ID=42`.

Frame QoS is `BEST_EFFORT` with `KEEP_LAST` and depth 1: late frames are dropped instead of piling up latency.

## Requirements

- Linux with ROS 2 (Humble or newer)
- `rmw_cyclonedds_cpp`
- [Tailscale](https://tailscale.com/) installed and connected on both machines
- Python 3.10+ with:
  - `opencv-python`
  - `mss`
  - `numpy`

All dependencies are installed by [`install_deps.sh`](https://github.com/mRangh/ros-2-adaptive-screen-streamer/blob/main/install_deps.sh) (see Usage).

## Project structure

```
screen_streamer/          # repository root (cloned as screen_streamer)
├── LICENSE
├── README.md
├── install_deps.sh
├── package.xml
├── setup.py
├── setup.cfg
├── resource/screen_streamer
└── screen_streamer/      # Python package
    ├── __init__.py
    ├── config.py
    ├── screen_publisher.py
    ├── screen_subscriber.py
    └── main.py
```

## Usage

First, create a ROS 2 workspace and clone the repository:

```bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone https://github.com/mRangh/ros-2-adaptive-screen-streamer.git screen_streamer
cd screen_streamer
chmod +x install_deps.sh && ./install_deps.sh
cd ~/ros2_ws
```

Then, build and source ROS 2 before running:

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
colcon build --symlink-install --packages-select screen_streamer
source install/setup.bash
```

### Stream your screen

On the machine that will **share** its screen:

```bash
ros2 run screen_streamer stream --publish --ip <VIEWER_TAILSCALE_IP>
```

### Watch another machine's screen

On the machine that will **watch**, provide the hostname of the machine that is streaming and its address on the tailnet:

```bash
ros2 run screen_streamer stream --host <PUBLISHER_HOSTNAME> --ip <PUBLISHER_TAILSCALE_IP>
```

> The hostname is sanitized (any character outside `[a-zA-Z0-9_]` becomes `_`) because it is used as the ROS namespace. Use the same hostname the publisher uses internally (the machine's `hostname`).

### Publish and watch at the same time

```bash
ros2 run screen_streamer stream --publish --host <OTHER_HOSTNAME> --ip <OTHER_TAILSCALE_IP>
```

### Examples

```bash
# 60 FPS, main monitor, fixed 70% quality
ros2 run screen_streamer stream --publish --ip 100.64.0.2 --fps 60 --quality 70

# Windowless viewer (only receives and reports FPS back)
ros2 run screen_streamer stream --host my_friend_pc --ip 100.64.0.1 --headless
```

## Arguments

| Argument      | Description                                                       | Default  |
|---------------|-------------------------------------------------------------------|----------|
| `--publish`   | Publish this machine's screen                                     | off      |
| `--host`      | Hostname of the machine whose screen will be watched              | —        |
| `--ip`        | Peer's Tailscale IP, used for CycloneDDS unicast discovery        | —        |
| `--fps`       | Target frame rate                                                 | `30`     |
| `--monitor`   | Monitor index (`0` = all monitors combined, `1` = main, …)        | `1`      |
| `--quality`   | Fixed JPEG quality (0–100) or `auto`                              | `auto`   |
| `--headless`  | Don't open the video window on the subscriber                     | off      |

You must provide `--publish`, `--host`, or both.

### Auto mode parameters

Defined in `config.py` (`StreamConfig`):

| Parameter            | Value | Description                |
|----------------------|-------|----------------------------|
| `start_jpeg_quality` | 40    | Initial quality            |
| `min_jpeg_quality`   | 10    | Quality floor              |
| `max_jpeg_quality`   | 90    | Quality ceiling            |

## Troubleshooting

**Nodes can't see each other.**
Check that Tailscale is up (`tailscale status`), that the interface is named `tailscale0`, and that `--ip` points to the correct peer. Since multicast is disabled, discovery depends entirely on that IP.

**Low FPS or stuttering video.**
Large frames are fragmented into UDP packets and, with `BEST_EFFORT`, losing a single fragment drops the whole frame. `auto` mode lowers quality to compensate. Increasing the kernel receive buffer may also help:

```bash
sudo sysctl -w net.core.rmem_max=26214400
```

**Invalid namespace error.**
ROS namespaces cannot start with a digit. If the hostname starts with a number, rename the machine or adjust the sanitizing function in `config.py`.

**`IndexError` when choosing a monitor.**
The index passed to `--monitor` doesn't exist. Use `0` for all monitors or `1` for the main one.

## Security

Any node reachable in ROS domain `42` can subscribe to the topic and see the streamed screen. Restrict access through Tailscale ACLs and only share your screen with machines you trust.

## License

Licensed under the [Apache License 2.0](https://github.com/mRangh/ros-2-adaptive-screen-streamer/blob/main/LICENSE)
