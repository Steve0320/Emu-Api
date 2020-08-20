import serial
import threading
import time

class Emu:

    def __init__(self):
        self.channel_open = False
        self.serial_port = None
        self.thread_handle = None
        self.stop_thread = False

    # Open communication channel
    def start_serial(self, port_name):

        if self.channel_open:
            return

        self.serial_port = self.__create_serial(port_name)
        self.thread_handle = threading.Thread(target=self.__communication_thread)
        self.thread_handle.start()
        self.channel_open = True

    # Close the communication channel
    def stop_serial(self):

        if not self.channel_open:
            return

        self.stop_thread = True
        self.thread_handle.join()
        self.thread_handle = None
        self.serial_port.close()
        self.serial_port = None

    # Internal helper for opening serial channel to device
    def __create_serial(self, port):
        baud_rate = 115200
        timeout = 1
        return serial.Serial(port, baud_rate, timeout)

    # Main communication thread - handles all asynchronous messaging
    def __communication_thread(self):
        while True:
            if self.stop_thread:
                print("Stopping thread")
                return
            print("TODO")
            time.sleep(10)
