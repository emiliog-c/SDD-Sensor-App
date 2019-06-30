#!/usr/bin/python3

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import Adafruit_DHT
import Adafruit_BMP.BMP085 as BMP085
import time
import sys

# Arguments  sensor_id host_name root_ca private_key cert_file
sensor_id = sys.argv[1]

# Sensor 4 uses a Nova SDS-011 sensor, all other nodes use Honeywell sensors
if sensor_id == '4':
  from sds011 import SDS011
  DEFAULT_SERIAL_PORT = "/dev/serial0" # Serial port to use if no other specified
  DEFAULT_BAUD_RATE = 9600 # Serial baud rate to use if no other specified
  DEFAULT_SERIAL_TIMEOUT = 2 # Serial timeout to use if not specified
  DEFAULT_READ_TIMEOUT = 1 #How long to sit looking for the correct character sequence.
else:
  import honeywell

# A random programmatic client ID.
MQTT_CLIENT = "Sensor{:s}RPiZeroW".format(sensor_id)

# The unique hostname that AWS IoT generated for 
# this device.
HOST_NAME = sys.argv[2] #"a3n039lf58a27m-ats.iot.ap-southeast-2.amazonaws.com"

# The relative path to the correct root CA file for AWS IoT, 
# that you have already saved onto this device.
# ROOT_CA = "AmazonRootCA1.pem"
ROOT_CA = sys.argv[3] #"/home/pi/root-CA.crt"

# The relative path to your private key file that 
# AWS IoT generated for this device, that you 
# have already saved onto this device.
PRIVATE_KEY = sys.argv[4] # "/home/pi/Sensor1.private.key"

# The relative path to your certificate file that 
# AWS IoT generated for this device, that you 
# have already saved onto this device.
CERT_FILE = sys.argv[5] # "/home/pi/Sensor1.cert.pem"

# A programmatic client handler name prefix.
MQTT_HANDLER = "Sensor{:s}RPi".format(sensor_id)

# Automatically called whenever the client is updated.
def myClientUpdateCallback(payload, responseStatus, token):
  print()
  print('UPDATE: $aws/things/' + MQTT_HANDLER +
    '/client/update/#')
  print("payload = " + payload)
  print("responseStatus = " + responseStatus)
  print("token = " + token)

# Create, configure, and connect to a client.
myClient = AWSIoTMQTTClient(MQTT_CLIENT)
myClient.configureEndpoint(HOST_NAME, 8883)
myClient.configureCredentials(ROOT_CA, PRIVATE_KEY,
  CERT_FILE)
myClient.configureConnectDisconnectTimeout(20)
myClient.configureMQTTOperationTimeout(10)
myClient.connect()
myClient.publish("sensors/info", '{{"sensor":"{:s}", "info":"connected"}}'.format(sensor_id), 1)

# Represents the GPIO21 pin on the Raspberry Pi.
# channel = 21

# Use the GPIO BCM pin numbering scheme.
# GPIO.setmode(GPIO.BCM)

# Receive input signals through the pin.
# GPIO.setup(channel, GPIO.IN)

# Sensor 4 uses a Nova SDS-011 sensor, all others use Honeywell sensors
if sensor_id == '4':
  # setup Nova SDS-011 sensor
  sds = SDS011(DEFAULT_SERIAL_PORT, use_query_mode=True)
else:
  # setup Honeywell sensor
  myClient.publish("sensors/info", '{{"sensor":"{:s}", "info":"initialising Honeywell sensor"}}'.format(sensor_id), 1)
  hw = honeywell.Honeywell()
  myClient.publish("sensors/info", '{{"sensor":"{:s}", "info":"starting particulate measurements"}}'.format(sensor_id), 1)
  hw.start_measuring()

# setup BMP180 temp and air pressure sensor
myClient.publish("sensors/info", '{{"sensor":"{:s}", "info":"initialising BMP180 sensor"}}'.format(sensor_id), 1)
bmp = BMP085.BMP085(mode=BMP085.BMP085_ULTRAHIGHRES)

while True:
  humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 17)
  # print(humidity, temperature)
  if humidity is None or temperature is None:
    myClient.publish("sensors/info", '{{"sensor":{:s}, "info":"DHT22 reading failed"}}'.format(sensor_id), 1)
    # re-try after a few seconds
    time.sleep(5)
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 17)
    if humidity is None or temperature is None:
      myClient.publish("sensors/info", '{{"sensor":{:s}, "info":"DHT22 reading also failed on 1st retry"}}'.format(sensor_id), 1)
      # re-try after a few seconds
      time.sleep(5)
      humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 17)
      if humidity is None or temperature is None:
        myClient.publish("sensors/info", '{{"sensor":{:s}, "info":"DHT22 reading failed again on 2nd retry"}}'.format(sensor_id), 1)
  # read the BMP180 sensor
  bmp180_temperature = bmp.read_temperature()
  bmp180_airpressure = bmp.read_pressure()

  if sensor_id == '4':
    # read the Nova SDS-011 sensor
    sds_results = sds.query()
  else:
    # read the Honeywell sensor
    pm_ts, pm10, pm25 = str(hw.read()).split(",")

  print(humidity, temperature, pm_ts, pm25, pm10, bmp180_temperature, bmp180_airpressure)
  if True:
    payload = '{{"sensor":"{:s}","timestamp":"{:s}","temperature":{:f},"humidity":{:f},"pm25":{:d},"pm10":{:d},"bmp180_temperature":{:f},"bmp180_airpressure":{:f}}}'.format(sensor_id, pm_ts,temperature, humidity,int(pm25),int(pm10), bmp180_temperature, bmp180_airpressure)
    try:
      myClient.publish("sensors/data", payload, 1)
    except:
      print("Unable to publish payload, will try again next round")

  # Wait for this test value to be added.
  time.sleep(15)

