# Emu-Api

This library allows communication with a Rainforest Automation EMU-2 device.
It is a rewrite of Rainforest's Emu-Serial-API in Python 3, and follows a similar architectural pattern where possible.

### Usage
First, import this library into your project using `from emu import Emu`. Then, instantiate a new
instance using `new Emu(<serial port name>)`, where the serial port name is the platform-specific device that
you wish to use. Note that unlike Rainforest's library, we do not attempt to detect the host platform or set
any port prefixes - this means that the full name of the device (prefixed with `COM` for Windows or `/dev` for OSX
and Linux, usually) must be used.

During construction, the serial channel is automatically opened. 