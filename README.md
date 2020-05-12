# Dark Spot Mapper

[![pipeline status](https://gitlab.com/AgenttiX/vxl-dark-spot-mapper/badges/master/pipeline.svg)](https://gitlab.com/AgenttiX/vxl-dark-spot-mapper/commits/master)
[![coverage report](https://gitlab.com/AgenttiX/vxl-dark-spot-mapper/badges/master/coverage.svg)](https://gitlab.com/AgenttiX/vxl-dark-spot-mapper/commits/master)

Dark Spot Mapper is a measurement system for imaging laser wafers and samples.
It consists of a camera and a three-axis linear stage system.

Developed by Mika Mäki 2016-2020 for the Optoelectronics Research Centre of Tampere University.

As of 2020 the software is fully functional, but the user interface (dark_spot_mapper.py) is waiting for a major rework.

## Cameras
Supported libraries are National Instruments NI Vision / IMAQdx and OpenCV (USB webcams, FireWire etc.).
OpenCV is recommended, as the National Instrumenst support is Windows-only and deprecated.
FireWire support is not included in the OpenCV available from PyPI, and custom binaries have to be used instead.
Docker-based build scripts for generating these binaries are provided in the repository.
They have been confirmed to work on Linux, but on Windows they have not yet been properly tested.

## Linear tages
Currently this software supports only [SimpleMotion V1](https://granitedevices.com/wiki/SimpleMotion_library_versions) linear stages.
Supported platforms are Linux (x86_64, arm32, arm64) and Windows (x86, x86_64).
The ARM Linux support is tailored for the Raspberry Pi.
The included binaries have been generated using the Docker build scripts of this repository.

On Linux, if SimpleMotion cannot find the motor drivers (and FTDI driver cannot find the USB adapters),
check if there are USB serial device such as ttyUSB0 in /dev. If there are, it means that
the kernel libFTDI driver has taken over the devices and the D2XX driver included in SimpleMotion
cannot therefore talk to them. To resolve this, you'll have to copy the udev rule
`99-simplemotion.rules` to `/etc/udev/rules.d`
Then run
`udevadm control --reload-rules && udevadm trigger`
to apply the changes.
This rule also gives the proper permissions for the devices, but you may have to allow your user to use the serial
ports with the command
`sudo adduser YOUR_USERNAME dialout`

The udev rule may not be enough to keep libFTDI off the adapters, and you may have to disable the kernel modules with
`sudo modprobe -r ftdi_sio` and
`sudo modprobe -r usbserial`.
To make the disabling of the kernel modules permanent, edit the file
sudo nano /etc/modprobe.d/blacklist
and add the lines
`blacklist ftdi_sio` and
`blacklist usbserial`
Then run
`sudo update-initramfs -u`
to apply the changes after the next reboot.

If you have compiled the Linux binaries with Alpine and you run them on Ubuntu,
you have to install the package "musl-dev".
You will also have to manually create a symlink with
`sudo ln -s /usr/lib/x86_64-linux-musl/libc.so /usr/lib/libc.musl-x86_64.so.1`.
