from setuptools import find_packages, setup

package_name = 'screen_streamer'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='mrangh',
    maintainer_email='marcoantonioranghetti@gmail.com',
    description='Screen streaming between machines using ROS 2, CycloneDDS, and Tailscale. One machine publishes its own screen as a sensor_msgs/CompressedImage (JPEG) and another subscribes and displays the video in real time. The JPEG quality is adjusted automatically based on the FPS the viewer is actually able to receive.',
    license='Apache License 2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'stream = screen_streamer.main:main'
        ],
    },
)
