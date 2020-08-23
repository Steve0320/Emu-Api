import serial
import threading
from xml.etree import ElementTree
import time
import response_entities


class Emu:

    def __init__(self, debug=False, synchronous=False):

        # Internal communication
        self._channel_open = False
        self._serial_port = None
        self._thread_handle = None
        self._stop_thread = False

        self.debug = debug
        self.synchronous = synchronous

        # Data, updated asynchronously by thread, keyed
        # by root element. These are defined by classes
        # in response_entities.py
        self._data = {}

        # TODO: Implement history mechanism

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
    # argument, and any additional params as a dict. Will return immediately
    # unless the synchronous attribute on the library is true, in which case
    # it will return data when available, or None if the timeout has elapsed.
    def issue_command(self, command, params=None, return_class=None, timeout=5, poll_factor=2):

        # TODO: Ensure stream open

        root = ElementTree.Element('Command')
        name_field = ElementTree.SubElement(root, 'Name')
        name_field.text = command

        if params is not None:
            for k, v in params.items():
                if v is not None:
                    field = ElementTree.SubElement(root, k)
                    field.text = v

        bin_string = ElementTree.tostring(root)

        if (not self.synchronous) or return_class is None:
            if self.debug:
                print("Object is in asynchronous mode or command does not have return type - not waiting for response")
            self._serial_port.write(bin_string)
            return True

        # Do our best to return results synchronously
        tag = return_class.tag_name()

        # Invalidate current response
        cur = self._data.get(tag)
        if cur is not None:
            cur.fresh = False

        self._serial_port.write(bin_string)

        step = 1.0 / poll_factor
        for i in range(0, timeout * poll_factor):
            d = self._data.get(tag)
            if d is not None and d.fresh:
                return d
            else:
                time.sleep(step)

        return None

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

    def restart(self):
        return self.issue_command('restart')

    # Dangerous! Will decommission device!
    def factory_reset(self):
        return self.issue_command('factory_reset')

    def get_connection_status(self):
        return self.issue_command('get_connection_status', return_class=response_entities.ConnectionStatus)

    def get_device_info(self):
        return self.issue_command('get_device_info', return_class=response_entities.DeviceInfo)

    def get_schedule(self, mac=None, event=None):

        if event not in['time', 'price', 'demand', 'summation', 'message']:
            raise ValueError('Valid events are time, price, demand, summation, or message')

        opts = {'MeterMacId': mac, 'Event': event}
        return self.issue_command('get_schedule', opts, return_class=response_entities.ScheduleInfo)

    def set_schedule(self, mac=None, event=None, frequency=10, enabled=True):

        if event not in ['time', 'price', 'demand', 'summation', 'message']:
            raise ValueError('Valid events are time, price, demand, summation, or message')

        opts = {
            'MeterMacId': mac,
            'Event': event,
            'Frequency': self._format_hex(frequency),
            'Enabled': self._format_yn(enabled)
        }
        return self.issue_command('set_schedule', opts)

    def set_schedule_default(self, mac=None, event=None):

        if event not in ['time', 'price', 'demand', 'summation', 'message']:
            raise ValueError('Valid events are time, price, demand, summation, or message')

        opts = {'MeterMacId': mac, 'Event': event}
        return self.issue_command('set_schedule_default', opts)

    def get_meter_list(self):
        return self.issue_command('get_meter_list', return_class=response_entities.MeterList)

    ##########################
    #     Meter Commands     #
    ##########################

    def get_meter_info(self, mac=None):
        opts = {'MeterMacId': mac}
        return self.issue_command('get_meter_info', opts, return_class=response_entities.MeterInfo)

    def get_network_info(self):
        return self.issue_command('get_network_info', return_class=response_entities.NetworkInfo)

    def set_meter_info(self, mac=None, nickname=None, account=None, auth=None, host=None, enabled=None):

        opts = {
            'MeterMacId': mac,
            'NickName': nickname,
            'Account': account,
            'Auth': auth,
            'Host': host,
            'Enabled': self._format_yn(enabled)
        }
        return self.issue_command('set_meter_info', opts)

    ############################
    #       Time Commands      #
    ############################

    def get_time(self, mac=None, refresh=True):
        opts = {'MeterMacId': mac, 'Refresh': self._format_yn(refresh)}
        return self.issue_command('get_time', opts, return_class=response_entities.TimeCluster)

    def get_message(self, mac=None, refresh=True):
        opts = {'MeterMacId': mac, 'Refresh': self._format_yn(refresh)}
        return self.issue_command('get_message', opts, return_class=response_entities.MessageCluster)

    def confirm_message(self, mac=None, message_id=None):

        if message_id is None:
            raise ValueError('Message id is required')

        opts = {'MeterMacId': mac, 'Id': self._format_hex(message_id)}
        return self.issue_command('confirm_message', opts)

    #########################
    #     Price Commands    #
    #########################

    def get_current_price(self, mac=None, refresh=True):
        opts = {'MeterMacId': mac, 'Refresh': self._format_yn(refresh)}
        return self.issue_command('get_current_price', opts, return_class=response_entities.PriceCluster)

    # Price is in cents, w/ decimals (e.g. "24.373")
    def set_current_price(self, mac=None, price="0.0"):

        parts = price.split(".", 1)
        if len(parts) == 1:
            trailing = 2
            price = int(parts[0])
        else:
            trailing = len(parts[1]) + 2
            price = int(parts[0] + parts[1])

        opts = {
            'MeterMacId': mac,
            'Price': self._format_hex(price),
            'TrailingDigits': self._format_hex(trailing, digits=2)
        }
        return self.issue_command('set_current_price', opts)

    ###############################
    #   Simple Metering Commands  #
    ###############################

    def get_instantaneous_demand(self, mac=None, refresh=True):
        opts = {'MeterMacId': mac, 'Refresh': self._format_yn(refresh)}
        return self.issue_command('get_instantaneous_demand', opts, return_class=response_entities.InstantaneousDemand)

    def get_current_summation_delivered(self, mac=None, refresh=True):
        opts = {'MeterMacId': mac, 'Refresh': self._format_yn(refresh)}
        return self.issue_command('get_current_summation_delivered', opts, return_class=response_entities.CurrentSummationDelivered)

    def get_current_period_usage(self, mac=None):
        opts = {'MeterMacId': mac}
        return self.issue_command('get_current_period_usage', opts, return_class=response_entities.CurrentPeriodUsage)

    def get_last_period_usage(self, mac=None):
        opts = {'MeterMacId': mac}
        return self.issue_command('get_last_period_usage', opts, return_class=response_entities.LastPeriodUsage)

    def close_current_period(self, mac=None):
        opts = {'MeterMacId': mac}
        return self.issue_command('close_current_period', opts)

    def set_fast_poll(self, mac=None, frequency=4, duration=20):
        opts = {
            'MeterMacId': mac,
            'Frequency': self._format_hex(frequency, digits=4),
            'Duration': self._format_hex(duration, digits=4)
        }
        return self.issue_command('set_fast_poll', opts)
