#!/bin/bash

curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --ssh

sudo apt update
sudo apt install -y ros-$ROS_DISTRO-cv-bridge ros-$ROS_DISTRO-sensor-msgs ros-$ROS_DISTRO-rmw-cyclonedds-cpp

pip3 install mss opencv-python numpy

echo "All dependencies installed! Your machine's IP is: $(tailscale ip -4)"
