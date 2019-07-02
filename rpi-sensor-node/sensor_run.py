#!/usr/bin/python3

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import Adafruit_DHT
import Adafruit_BMP.BMP085 as BMP085
import time
import datetime
import sys

# Arguments  sensor_id host_name root_ca private_key cert_file
sensor_id = sys.argv[1]

# A random programmatic client ID.
MQTT_CLIENT = "Sensor{:s}RPiZeroW".format(sensor_id)

# The unique hostname that AWS IoT generated for this device.
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

# The type of particulate sensor used. Valid values are
# Honeywell or SDS011 (case-sensitive)
particulate_sensor_type = sys.argv[6]

# functions we need later
def get_local_timestamp():
  # get a timestamp for the local time on the sensor
  local_ts = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
  return(local_ts)

def trimmedMean(lst, numberToTrim=3):
  # first sort the list passed to this function, but it may contain Nones and a mixture of
  # integers and floats, which cause the sort() function to fail. So instead use this
  # sorted list containing None trick from https://stackoverflow.com/questions/18411560/python-sort-list-with-none-at-the-end
  sortedLst = sorted(lst, key=lambda x: float('inf') if x is None else float(x))
  # trim it by slicing off number_to_trim elements from each end
  trimmedLst = sortedLst[numberToTrim:-numberToTrim]
  # now get the average and return it
  return( sum(trimmedLst) / len(trimmedLst) )

# Import the right library for the particulate sensor type
if particulate_sensor_type == 'Honeywell':
  import honeywell
elif particulate_sensor_type == 'SDS011':
  from sds011 import SDS011
  DEFAULT_SERIAL_PORT = "/dev/serial0" # Serial port to use if no other specified
  DEFAULT_BAUD_RATE = 9600 # Serial baud rate to use if no other specified
  DEFAULT_SERIAL_TIMEOUT = 2 # Serial timeout to use if not specified
  DEFAULT_READ_TIMEOUT = 1 # How long to sit looking for the correct character sequence.

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
myClient.configureCredentials(ROOT_CA, PRIVATE_KEY, CERT_FILE)
myClient.configureConnectDisconnectTimeout(20)
myClient.configureMQTTOperationTimeout(10)
myClient.connect()
time.sleep(10)
myClient.publish("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"MQTT client connected"}}'.format(sensor_id,get_local_timestamp()), 1)
time.sleep(10)

# Represents the GPIO21 pin on the Raspberry Pi.
# channel = 21

# Use the GPIO BCM pin numbering scheme.
# GPIO.setmode(GPIO.BCM)

# Receive input signals through the pin.
# GPIO.setup(channel, GPIO.IN)

# set up the particulate sensors
if particulate_sensor_type == 'SDS011':
  # setup Nova SDS-011 sensor
  myClient.publish("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"initialising Nova SDS-011 sensor"}}'.format(sensor_id,get_local_timestamp()), 1)
  time.sleep(10)
  sds = SDS011(DEFAULT_SERIAL_PORT, use_query_mode=True)
elif particulate_sensor_type == 'Honeywell':
  # setup Honeywell sensor
  myClient.publish("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"initialising Honeywell sensor"}}'.format(sensor_id,get_local_timestamp()), 1)
  time.sleep(10)
  hw = honeywell.Honeywell()
  myClient.publish("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"starting particulate measurements"}}'.format(sensor_id,get_local_timestamp()), 1)
  time.sleep(10)
  hw.start_measuring()
else:
  myClient.publish("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"no particulate sensor was initialised"}}'.format(sensor_id,get_local_timestamp()), 1)
  time.sleep(10)

# setup BMP180 temp and air pressure sensor
myClient.publish("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"initialising BMP180 sensor"}}'.format(sensor_id,get_local_timestamp()), 1)
time.sleep(10)
bmp = BMP085.BMP085(mode=BMP085.BMP085_ULTRAHIGHRES) # ultra-high res mode seems to work fine

# main loop forever
while True:
  # the idea is to take 20 readings at 15 second intervals from each sensor type and store the results
  # for each sensor type in a list, and then sort that list of values and discard the lowest three and highest 
  # three readings, then calculate the average of the remaining readings. This is called a trimmed mean.
  # This should get rid of most erroneous measurements caused by sensor glitches will be discarded, and the data 
  # will be a lot cleaner without spikes of obviously incorrect readings. This data cleaning could be done
  # after the data have been collected into the central database, bt might as well do it at the
  # point of data collection on each sensor device

  # first set up lists to hold the readings for each sensor type
  humidityReadings = list() # from the DHT22 sensor device
  temperatureReadings = list() # from the DHT22 device
  temperatureBmp180Readings = list() # from the BMP180 device
  airpressureReadings = list() # from the BMP180 device
  pm10Readings = list() # air particulates
  pm25Readings = list() # air particulates

  # now loop for 20 times to take readings from each device and append the reading to the 
  # lists we just set up
  for t in range(20):

    # first get humidity and temp from the DHT22 device
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 17)
    # sometimes the DHT22 glitches and returns None as the readings, so check for that and
    # try again after a few seconds, and send a message to the sensors/info MQTT topic stream
    if humidity is None or temperature is None:
      # log a message to the sensors/info MQTT topic
      myClient.publish("sensors/info", '{{"sensor":{:s},"timestamp":"{:s}","info":"DHT22 reading failed"}}'.format(sensor_id, get_local_timestamp()), 1)
      # re-try after a few seconds
      time.sleep(3)
      humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 17)
      if humidity is None or temperature is None:
        # log a message to the sensors/info MQTT topic
        myClient.publish("sensors/info", '{{"sensor":{:s},"timestamp":"{:s}","info":"DHT22 reading also failed on 1st retry"}}'.format(sensor_id, get_local_timestamp()), 1)
        # re-try after a few more seconds
        time.sleep(10)
        humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 17)
        if humidity is None or temperature is None:
          # log a message to the sensors/info MQTT topic
          myClient.publish("sensors/info", '{{"sensor":{:s},"timestamp":"{:s}","info":"DHT22 reading failed again on 2nd retry"}}'.format(sensor_id, get_local_timestamp()), 1)
          time.sleep(10)
          # if still an error, then the value will be None, but it should be eliminated by the trimmed means procedure
    # add the readings to the lists
    humidityReadings.append(float(humidity))
    temperatureReadings.append(float(temperature))

    # now read the BMP180 sensor. This doesn't seem to glitch so don't bother trying to re-read it if it
    # returns None values
    bmp180_temperature = bmp.read_temperature()
    bmp180_airpressure = bmp.read_pressure()
    # add the readings to the lists
    airpressureReadings.append(float(bmp180_airpressure))
    temperatureBmp180Readings.append(float(bmp180_temperature))

    # finally read the particulate sensor device, using the correct driver for that device 
    if particulate_sensor_type == 'SDS011':
      # read the Nova SDS-011 sensor
      pm10, pm25 = str(sds.query())
    elif particulate_sensor_type == 'Honeywell':
      # read the Honeywell sensor, note that it also returns a timestamp but in UTC (Greenwich) time which we don't use
      pm_ts_utc, pm10, pm25 = str(hw.read()).split(",")
    else:
      # The particulate device type parameter on the command line must not be correct, so log it
      myClient.publish("sensors/info", '{{"sensor":{:s},"timestamp":"{:s}","info":"particulate device type parameter incorrect!"}}'.format(sensor_id, get_local_timestamp()), 1)
      time.sleep(600)
    # add the readings to the lists
    pm10Readings.append(float(pm10))
    pm25Readings.append(float(pm25))

    # now sleep for 15 seconds
    time.sleep(15)

  # at this point there should be 20 readings in lists for each of the measurement types
  # so get the trimmed mean of each of these lists
  meanHumidity = trimmedMean(humidityReadings)
  meanTemperature = trimmedMean(temperatureReadings)
  meanBmp180Temperature = trimmedMean(temperatureBmp180Readings)
  meanAirpressure = trimmedMean(airpressureReadings)
  meanPM10 = trimmedMean(pm10Readings)
  meanPM25 = trimmedMean(pm25Readings)
  # print out the clean data as a check
  print(get_local_timestamp(), meanHumidity, meanTemperature, meanPM25, meanPM10, meanBmp180Temperature, meanAirpressure)
  # assemble all these values into a JSON data payload string
  payload = '{{"sensor":"{:s}","timestamp":"{:s}","temperature":{:f},"humidity":{:f},"pm25":{:f},"pm10":{:f},"bmp180_temperature":{:f},"bmp180_airpressure":{:f}}}'.format(sensor_id, get_local_timestamp(),meanTemperature, meanHumidity,meanPM25,meanPM10,meanBmp180Temperature,meanAirpressure)
  try:
    myClient.publish("sensors/data", payload, 1)
  except:
    print("Unable to publish payload, will try again next round")

  # sleep for a few seconds before starting all over again
  time.sleep(3)

