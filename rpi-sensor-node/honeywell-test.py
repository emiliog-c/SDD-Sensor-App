# this is just test code, it is not part of the Sensor node

"""
    Wrapper classes for the Honeywell HPMA115S0.
    Florentin Bulot
    15/01/2019
    based on https://github.com/FEEprojects/plantower
"""

import logging
import time
from datetime import datetime, timedelta
from serial import Serial, SerialException

DEFAULT_SERIAL_PORT = "/dev/serial0" # Serial port to use if no other specified
DEFAULT_BAUD_RATE = 9600 # Serial baud rate to use if no other specified
DEFAULT_SERIAL_TIMEOUT = 2 # Serial timeout to use if not specified
DEFAULT_READ_TIMEOUT = 1 #How long to sit looking for the correct character sequence.

DEFAULT_LOGGING_LEVEL = logging.WARN

MSG_CHAR_1 = b'\x42' # First character to be recieved in a valid packet
MSG_CHAR_2 = b'\x4d' # Second character to be recieved in a valid packet
CMD_POS_ACK_CHAR = b'\xa5' # Character x2 to be recieved in a positive acknowledgement
CMD_NEG_ACK_CHAR = b'\x96' # Character x2 to be recieved in a negative acknowledgement


class HoneywellReading(object):
    """
        Describes a single reading from the Honeywell sensor
    """
    def __init__(self, line):
        """
            Takes a line from the Honeywell serial port and converts it into
            an object containing the data
        """
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.pm10 = round(line[8] * 256 + line[9], 1)
        self.pm25 = round(line[6] * 256 + line[7], 1)

    def __str__(self):
        return (
            "%s,%s,%s" %
            (self.timestamp, self.pm10, self.pm25))

class HoneywellException(Exception):
    """
        Exception to be thrown if any problems occur
    """
    pass

class Honeywell(object):
    """
        Actual interface to the HPMA115S0 sensor
    """
    def __init__(
            self, port=DEFAULT_SERIAL_PORT, baud=DEFAULT_BAUD_RATE,
            serial_timeout=DEFAULT_SERIAL_TIMEOUT,
            read_timeout=DEFAULT_READ_TIMEOUT,
            log_level=DEFAULT_LOGGING_LEVEL):
        """
            Setup the interface for the sensor
        """
        self.logger = logging.getLogger("HPMA115S0 Interface")
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
        self.logger.setLevel(log_level)
        self.port = port
        self.logger.info("Serial port: %s", self.port)
        self.baud = baud
        self.logger.info("Baud rate: %s", self.baud)
        self.serial_timeout = serial_timeout
        self.logger.info("Serial Timeout: %s", self.serial_timeout)
        self.read_timeout = read_timeout
        self.logger.info("Read Timeout: %s", self.read_timeout)
        try:
            self.serial = Serial(
                port=self.port, baudrate=self.baud,
                timeout=self.serial_timeout)
            self.logger.debug("Port Opened Successfully")
        except SerialException as exp:
            self.logger.error(str(exp))
            raise HoneywellException(str(exp))
        self.stop_measuring(check_ack=False)

    def start_measuring(self):
        """
            Starts the fan running in the sensor and enables auto-send mode.
        """
        self.serial.write(b'\x68\x01\x01\x96') # Send command to start measuring
        self.serial.flush() # flush the buffer
        self._check_cmd_ack("Sensor measurement start command failed")
        self.serial.write(b'\x68\x01\x40\x57') # Enable auto send
        self.serial.flush() # flush the buffer
        self._check_cmd_ack("Sensor auto-send enable command failed")

    def stop_measuring(self, check_ack=True):
        """
            Disables auto-send mode and stops the fan running in the sensor 
        """
        self.serial.write(b'\x68\x01\x20\x77') # Disable auto send
        self.serial.flush() # flush the buffer
        if check_ack:
            self._check_cmd_ack("Sensor auto-send disable command failed")
        self.serial.write(b'\x68\x01\x02\x95') # Send command to stop measuring
        self.serial.flush() # flush the buffer
        if check_ack:
            self._check_cmd_ack("Sensor measurement stop command failed")

    def set_log_level(self, log_level):
        """
            Enables the class logging level to be changed after it's created
        """
        self.logger.setLevel(log_level)

    def _check_cmd_ack(self, errormsg):
        """
            Checks acknowledgement for certain commands
        """
        ack_inp1 = self.serial.read() # read the next character
        print(ack_inp1)
        if ack_inp1 == CMD_POS_ACK_CHAR:
            ack_inp2 = self.serial.read() # read the next character
            print(ack_inp2)
            if ack_inp2 == CMD_POS_ACK_CHAR:
                self.logger.debug(errormsg)
            else:
                self.logger.error(errormsg)
                raise HoneywellException(errormsg)
        else:
            self.logger.error(errormsg)
            raise HoneywellException(errormsg)

    def _verify(self, recv):
        """
            Uses the last 2 bytes of the data packet from the Honeywell sensor
            to verify that the data recived is correct
        """
        calc = 0
        ord_arr = []
        for c in bytearray(recv[:-2]): #Add all the bytes together except the checksum bytes
            calc += c
            ord_arr.append(c)
        self.logger.debug(str(ord_arr))
        sent = (recv[-2] << 8) | recv[-1] # Combine the 2 bytes together
        if sent != calc:
            self.logger.error("Checksum failure %d != %d", sent, calc)
            raise HoneywellException("Checksum failure")

    def read(self, perform_flush=True):
        """
            Reads a line from the serial port and return
            if perform_flush is set to true it will flush the serial buffer
            before performing the read, otherwise, it'll just read the first
            item in the buffer
        """
        recv = b''
        start = datetime.utcnow() #Start timer
        if perform_flush:
            self.serial.flush() #Flush any data in the buffer
        while(
                datetime.utcnow() <
                (start + timedelta(seconds=self.read_timeout))):
            inp = self.serial.read() # Read a character from the input
            if inp == MSG_CHAR_1: # check it matches
                recv += inp # if it does add it to recieve string
                inp = self.serial.read() # read the next character
                if inp == MSG_CHAR_2: # check it's what's expected
                    recv += inp # att it to the recieve string
                    recv += self.serial.read(30) # read the remaining 30 bytes
                    self._verify(recv) # verify the checksum
                    return HoneywellReading(recv) # convert to reading object
            #If the character isn't what we are expecting loop until timeout
        raise HoneywellException("No message received")

# test the Honeywell sensor
print("Initialising...")
hw = Honeywell()
#print("Wait 15 seconds...")
#time.sleep(15)
#print("Stop measuring")
#hw.stop_measuring()
#print("Wait 15 seconds...")
#time.sleep(15)
print("Start measuring")
hw.start_measuring()
#print("Wait 15 seconds...")
#time.sleep(15)
#print("Take a reading...")
#reading = hw.read()
#print(reading)
#print("Take a reading...")
#reading = hw.read()
#print(reading)
# print("Stop measuring")
# hw.stop_measuring()
print("Take a reading...")
while True:
    reading = hw.read()
    print(reading)
    time.sleep(5)

