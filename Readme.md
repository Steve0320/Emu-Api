# Emu-Api

This library allows communication with a Rainforest Automation EMU-2 device.
It is a rewrite of Rainforest's Emu-Serial-API in Python 3, and follows a similar architectural pattern where possible.

### Usage
First, import this library into your project using `from emu import Emu`, and instantiate a new instance using `new Emu()`.

As in Rainforest's library, we do not automatically start communication once the main object is instantiated. This
is done because the EMU-2 constantly pushes data to us over the serial connection, so we want to give the consumer
control over when this channel is opened. Before any commands are issued, the `start_serial(<serial port>)` method
must be called to open the serial port and begin receiving data.

The serial port name is the platform-specific device that
you wish to use. Note that unlike Rainforest's library, we do not attempt to detect the host platform or set
any port prefixes - this means that the full name of the device (prefixed with `COM` for Windows or `/dev` for OSX
and Linux, usually) must be used.