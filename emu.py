import serial
import threading
from xml.etree import ElementTree
import response_entities


class Emu:

    def __init__(self, debug=False):

        # Internal communication
        self._channel_open = False
        self._serial_port = None
        self._thread_handle = None
        self._stop_thread = False

        self.debug = debug

        # Data, updated asynchronously by thread, keyed
        # by root element. These are defined by classes
        # in response_entities.py
        self.data = {}

    # Open communication channel
    def start_serial(self, port_name):

        if self._channel_open:
            return

        self._serial_port = self._create_serial(port_name)
        self._thread_handle = threading.Thread(target=self._communication_thread)
        self._thread_handle.start()
        self._channel_open = True

    # Close the communication channel
    def stop_serial(self):

        if not self._channel_open:
            return

        self._stop_thread = True
        self._thread_handle.join()
        self._thread_handle = None
        self._serial_port.close()
        self._serial_port = None

    # Issue a command to the device. Pass the command name as the first
    # argument, and any additional params as a dict.
    def issue_command(self, command, params=None):

        root = ElementTree.Element('Command')
        name_field = ElementTree.SubElement(root, 'Name')
        name_field.text = command

        if params is not None:
            for k, v in params.items():
                field = ElementTree.SubElement(root, k)
                field.text = v

        bin_string = ElementTree.tostring(root)
        self._serial_port.write(bin_string)
        return True

    # Internal helper for opening serial channel to device
    def _create_serial(self, port):
        baud_rate = 115200
        timeout = 1
        return serial.Serial(port, baud_rate, timeout=timeout)

    # Main communication thread - handles all asynchronous messaging
    def _communication_thread(self):
        while True:

            if self._stop_thread:
                self._stop_thread = False
                return

            # Update read data, ignoring timeouts
            bin_lines = self._serial_port.readlines()

            if len(bin_lines) > 0:

                try:
                    tree = ElementTree.fromstringlist(bin_lines)
                except ElementTree.ParseError:
                    print("Malformed XML " + bin_lines.decode('UTF-8'))
                    continue

                if self.debug:
                    ElementTree.dump(tree)

                response_type = tree.tag
                klass = response_entities.Entity.tag_to_class(response_type)
                if klass is None:
                    print("Unsupported tag " + response_type)
                else:
                    self.data[response_type] = klass(tree)
