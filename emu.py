import serial
import threading
from xml.etree import ElementTree
import response_entities


class Emu:

    def __init__(self, debug=False, history_length=10):

        # Internal communication
        self._channel_open = False
        self._serial_port = None
        self._thread_handle = None
        self._stop_thread = False

        self.debug = debug

        # Data, updated asynchronously by thread, keyed
        # by root element. These are defined by classes
        # in response_entities.py
        self._data = {}

        # TODO: History, holds last history_length responses.
        self.history_length = history_length
        # self.history = {}

    # Get the latest response for the given type. Also marks
    # the object as stale.
    def get_response(self, command):
        e = self._data.get(command)
        if e is None:
            return None
        else:
            e.fresh = False
            return e

    # Open communication channel
    def start_serial(self, port_name):

        if self._channel_open:
            return True

        try:
            self._serial_port = self._create_serial(port_name)
        except serial.serialutil.SerialException:
            return False

        self._thread_handle = threading.Thread(target=self._communication_thread)
        self._thread_handle.start()
        self._channel_open = True
        return True

    # Close the communication channel
    def stop_serial(self):

        if not self._channel_open:
            return True

        self._stop_thread = True
        self._thread_handle.join()
        self._thread_handle = None
        self._serial_port.close()
        self._serial_port = None
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
                    # TODO: Handle multiple fragments correctly (get_schedule)
                    tree = ElementTree.fromstringlist(bin_lines)
                except ElementTree.ParseError:
                    if self.debug:
                        print("Malformed XML " + b''.join(bin_lines).decode('ASCII'))
                    continue

                if self.debug:
                    ElementTree.dump(tree)

                response_type = tree.tag
                klass = response_entities.Entity.tag_to_class(response_type)
                if klass is None:
                    if self.debug:
                        print("Unsupported tag " + response_type)
                    continue
                else:
                    self._data[response_type] = klass(tree)

    # Issue a command to the device. Pass the command name as the first
    # argument, and any additional params as a dict.
    def issue_command(self, command, params=None):

        root = ElementTree.Element('Command')
        name_field = ElementTree.SubElement(root, 'Name')
        name_field.text = command

        if params is not None:
            for k, v in params.items():
                if v is not None:
                    field = ElementTree.SubElement(root, k)
                    field.text = v

        bin_string = ElementTree.tostring(root)
        self._serial_port.write(bin_string)
        return True

    # Convert boolean to Y/N for commands
    def _format_yn(self, value):
        if value is None:
            return None
        if value:
            return 'Y'
        else:
            return 'N'

    # Convert an integer into a hex string
    def _format_hex(self, num, digits=8):
        return "0x{:0{digits}x}".format(num, digits=digits)

    # The following are convenience methods for sending commands. Commands
    # can also be sent manually using the generic issue_command method.

    #################################
    #         Raven Commands        #
    #################################

    def initialize(self):
        self.issue_command('initialize')

    def factory_reset(self):
        self.issue_command('factory_reset')

    def get_connection_status(self):
        self.issue_command('get_connection_status')

    def get_device_info(self):
        self.issue_command('get_device_info')

    # TODO: This is currently broken unless event is specified
    def get_schedule(self, mac=None, event=None):

        if event not in['time', 'price', 'demand', 'summation', 'message']:
            raise ValueError('Valid events are time, price, demand, summation, or message')

        opts = {'MeterMacId': mac, 'Event': event}
        self.issue_command('get_schedule', opts)

    def set_schedule(self, mac=None, event=None, frequency=10, enabled=True):

        if event not in ['time', 'price', 'demand', 'summation', 'message']:
            raise ValueError('Valid events are time, price, demand, summation, or message')

        opts = {
            'MeterMacId': mac,
            'Event': event,
            'Frequency': self._format_hex(frequency),
            'Enabled': self._format_yn(enabled)
        }
        self.issue_command('set_schedule', opts)

    def set_schedule_default(self, mac=None, event=None):

        if event not in ['time', 'price', 'demand', 'summation', 'message']:
            raise ValueError('Valid events are time, price, demand, summation, or message')

        opts = {'MeterMacId': mac, 'Event': event}
        self.issue_command('set_schedule_default', opts)

    def get_meter_list(self):
        self.issue_command('get_meter_list')

    ##########################
    #     Meter Commands     #
    ##########################

    def get_meter_info(self, mac=None):
        opts = {'MeterMacId': mac}
        self.issue_command('get_meter_info', opts)

    def get_network_info(self):
        self.issue_command('get_network_info')

    def set_meter_info(self, mac=None, nickname=None, account=None, auth=None, host=None, enabled=None):

        opts = {
            'MeterMacId': mac,
            'NickName': nickname,
            'Account': account,
            'Auth': auth,
            'Host': host,
            'Enabled': self._format_yn(enabled)
        }
        self.issue_command('set_meter_info', opts)

    ############################
    #       Time Commands      #
    ############################

    def get_time(self, mac=None, refresh=True):
        opts = {'MeterMacId': mac, 'Refresh': self._format_yn(refresh)}
        self.issue_command('get_time', opts)

    def get_message(self, mac=None, refresh=True):
        opts = {'MeterMacId': mac, 'Refresh': self._format_yn(refresh)}
        self.issue_command('get_message', opts)

    def confirm_message(self, mac=None, message_id=None):

        if message_id is None:
            raise ValueError('Message id is required')

        opts = {'MeterMacId': mac, 'Id': self._format_hex(message_id)}
        self.issue_command('confirm_message', opts)

    #########################
    #     Price Commands    #
    #########################

    def get_current_price(self, mac=None, refresh=True):
        opts = {'MeterMacId': mac, 'Refresh': self._format_yn(refresh)}
        self.issue_command('get_current_price', opts)

    def set_current_price(self, mac=None, price=None, trailing_digits=0):
        opts = {
            'MeterMacId': mac,
            'Price': self._format_hex(price),
            'TrailingDigits': self._format_hex(trailing_digits, digits=2)
        }
        self.issue_command('set_current_price', opts)

    ###############################
    #   Simple Metering Commands  #
    ###############################

    def get_instantaneous_demand(self, mac=None, refresh=True):
        opts = {'MeterMacId': mac, 'Refresh': self._format_yn(refresh)}
        self.issue_command('get_instantaneous_demand', opts)

    def get_current_summation_delivered(self, mac=None, refresh=True):
        opts = {'MeterMacId': mac, 'Refresh': self._format_yn(refresh)}
        self.issue_command('get_current_summation_delivered', opts)

    def get_current_period_usage(self, mac=None):
        opts = {'MeterMacId': mac}
        self.issue_command('get_current_period_usage', opts)

    def get_last_period_usage(self, mac=None):
        opts = {'MeterMacId': mac}
        self.issue_command('get_last_period_usage', opts)

    def close_current_period(self, mac=None):
        opts = {'MeterMacId': mac}
        self.issue_command('close_current_period', opts)

    def set_fast_poll(self, mac=None, frequency=4, duration=20):
        opts = {
            'MeterMacId': mac,
            'Frequency': self._format_hex(frequency, digits=4),
            'Duration': self._format_hex(duration, digits=4)
        }
        self.issue_command('set_fast_poll', opts)

    def get_profile_data(self, mac=None, periods=1, end_time=0, channel='Delivered'):

        if channel not in ['Delivered', 'Received']:
            raise ValueError('Channel must be Delivered or Received')

        opts = {
            'MeterMacId': mac,
            'NumberOfPeriods': self._format_hex(periods, digits=1),
            'EndTime': self._format_hex(end_time),
            'IntervalChannel': channel
        }
        self.issue_command('get_profile_data', opts)
