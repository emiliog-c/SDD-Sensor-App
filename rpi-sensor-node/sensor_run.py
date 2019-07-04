#!/usr/bin/python3
"""
name: sensor_run.py
author: Emilio Guevarra Churches
date: June and July 2019
license: see LICENSE file
description: this is the main code that runs on each sensor node in my SDD project. See
the README file for the project description.
"""

##################################################
# set-up section
##################################################

# import python libraries
# AWS MQTT protocol client for python
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
# Adafruit libraries for the DHT22 temp and humidity sensor
# and the BMP085/BMP180 temp and air pressure sensor
import Adafruit_DHT
import Adafruit_BMP.BMP085 as BMP085
# various utility libraries
import time
import datetime
import sys

# collect parameters passed from the command line
# parameters in order starting at 0 are:
# script filename
# sensor_id
# AWS IoT host_name
# AWS root_ca filename
# AWS IoT private_key filename
# AWS IoT cert_file

# sensor ID to identify this sensor node
sensor_id = sys.argv[1]
# we need to assign a unique client ID based on the sensor ID
# for use with the MQTT client (RPiZeroW is the type of 
# Raspberry Pi computer the node is running on
MQTT_CLIENT = "Sensor{:s}RPiZeroW".format(sensor_id)

# The unique hostname that AWS IoT generated for this device.
# should look like: a19nuo7ml0j5az-ats.iot.ap-southeast-2.amazonaws.com
HOST_NAME = sys.argv[2]

# The relative path to the correct root CA file for AWS IoT,
# should look like: /home/pi/root-CA.crt
ROOT_CA = sys.argv[3]

# The relative path to the private key file that
# AWS IoT generated for this device,
# should look like: /home/pi/Sensor1.private.key (but with correct sensor ID)
PRIVATE_KEY = sys.argv[4]

# The relative path to the certificate file that
# AWS IoT generated for this device,
# should look like: /home/pi/Sensor1.cert.pem
CERT_FILE = sys.argv[5]

# The type of particulate sensor used. Valid values are
# Honeywell or SDS011 (case-sensitive)
particulate_sensor_type = sys.argv[6]

# A programmatic client handler name prefix required by the AWS IoT MQTT client 
MQTT_HANDLER = "Sensor{:s}RPi".format(sensor_id)

##################################################
# define some functions we need later
##################################################

def get_local_timestamp():
  # get a timestamp for the local time (not UTC/GMT) on the sensor
  local_ts = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
  return(local_ts)

def trimmedMean(valuesList, numberToTrim=3):
  # calculate a trimmed mean of value in a list, see the main loop section below
  # for why this is needed and what it does
  # first sort the list passed to this function, but it may contain Nones and a mixture of
  # integers and floats, which cause the sort() function to fail. So instead use this trick
  # to sort lists containing integers, floats and Nones from
  # https://stackoverflow.com/questions/18411560/python-sort-list-with-none-at-the-end
  sortedLst = sorted(valuesList, key=lambda x: float('inf') if x is None else float(x))
  # trim it by slicing off number_to_trim elements from each end
  trimmedLst = sortedLst[numberToTrim:-numberToTrim]
  # now get the average and return it
  return(sum(trimmedLst) / len(trimmedLst))

##################################################
# AWS IoT MQTT client set-up and connection
##################################################

# create, configure, and connect to a client
# this code from the example code in an AWS tutorial on using MQTT in python
# create an instance of the AWS IoT MQTT client class
myClient = AWSIoTMQTTClient(MQTT_CLIENT)
# set various values (described in setup section above)
myClient.configureEndpoint(HOST_NAME, 8883)
myClient.configureCredentials(ROOT_CA, PRIVATE_KEY, CERT_FILE)
# keep trying to connect for 60 seconds
myClient.configureConnectDisconnectTimeout(60)
# keep trying to send a message for 60 seconds
myClient.configureMQTTOperationTimeout(60)
# recommended setings for automatic reconnect
myClient.configureAutoReconnectBackoffTime(1, 128, 20)
# number of messages to keep in the queue to be sent if MQTT client is offline
myClient.configureOfflinePublishQueueing(500, AWSIoTPyMQTT.DROP_OLDEST)
# how fast to draing the queue of stored messages when MQTT clinet reconnects
myClient.configureDrainingFrequency(1)
# define a function to be called when the MQTT client goes online
def myOnOnlineCallback():
  # print a message to the console
  print("MQTT client connected and online")
  # also send a MQTT message to the sensors/info topic
  # The payload of the message is formatted as JSON with values for
  # the sensor ID, the current date and time, and an information message as text
  myClient.publishAsync("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"MQTT client online"}}'.format(sensor_id,get_local_timestamp()),1)
  time.sleep(10)
# Register the function defined above to be called when the MQTT  goes online
myClient.onOnline = myOnOnlineCallback
def myOnOfflineCallback():
  # print a message to the console
  print("MQTT client disconnected and offline")
  # also send a MQTT message to the sensors/info topic
  myClient.publishAsync("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"MQTT client offline"}}'.format(sensor_id,get_local_timestamp()),1)
  time.sleep(10)
# Register the function defined above to be called when the MQTT  goes online
myClient.onOffline = myOnOfflineCallback
# tell the client to connect with AWS
# use 2400 seconds for the keep-alive which is much longer than the
# time between data sends, so the connection doesn't drop between
# each data send (publish)
myClient.connectAsync(keepAliveIntervalSecond=2400)
# seems to need a few seconds before the connection is ready to use
time.sleep(10)

# define a message publish acknowledgement callback function,
# called automatically when an acknowledgement of successful message
# publication is received when quality of service QoS is 1 (which requests ACKs)
def myPubackCallback(mid):
  print("Message ID {:d} sent and acknowledged".format(mid))

##################################################
# set up particulate sensor device
##################################################

# import the right library for the particulate sensor type for this node
if particulate_sensor_type == 'Honeywell':
  # the Honeywell driver already has serial port values set as required
  import honeywell
  # create an instance of the Honeywell driver class, this can sometimes fail
  # so log the failures
  try:
    hw = honeywell.Honeywell()
    print("Honeywell sensor initialised")
    # also send info message saying it is initialised
    myClient.publishAsync("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"initialised Honeywell sensor"}}'.format(sensor_id,get_local_timestamp()), 1)
    time.sleep(10)
  except:
    print("Honeywell sensor failed to initialise - bailing!")
    # also send info message saying it failed
    myClient.publishAsync("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"Honeywell sensor failed to initialise"}}'.format(sensor_id,get_local_timestamp()), 1)
    time.sleep(30)
    # exit the program so it is automatically restarted to try again
    sys.exit(1)
  # the Honeywell sensor also has to be told to start taking measurements
  try:
    hw.start_measuring()
    print("Honeywell sensor started measuring")
    myClient.publishAsync("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"Honeywell sensor started measuring"}}'.format(sensor_id,get_local_timestamp()), 1)
    time.sleep(10)
  except:
    print("Honeywell sensor failed to start measuring - bailing!")
    myClient.publishAsync("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"Honeywell sensor failed to start measuring"}}'.format(sensor_id,get_local_timestamp()), 1)
    time.sleep(30)
    # bail!
    sys.exit(1)
elif particulate_sensor_type == 'SDS011':
  from sds011 import SDS011
  # the SDS-011 driver needs various serial port values to be set as constants
  DEFAULT_SERIAL_PORT = "/dev/serial0" # Serial port to use if no other specified
  DEFAULT_BAUD_RATE = 9600 # Serial baud rate to use if no other specified
  DEFAULT_SERIAL_TIMEOUT = 2 # Serial timeout to use if not specified
  DEFAULT_READ_TIMEOUT = 1 # How long to sit looking for the correct character sequence.
  # set up Nova SDS-011 sensor
  # send an info message saying it is being initialised
  myClient.publishAsync("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"initialising Nova SDS-011 sensor"}}'.format(sensor_id,get_local_timestamp()), 1)
  time.sleep(10)
  # create an instance of the SDS011 driver class, this can also fail, if so, bail out of program  so it restarts
  try:
    sds = SDS011(DEFAULT_SERIAL_PORT, use_query_mode=True)
    print("Nova SDS-011 sensor initialised")
    myClient.publishAsync("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"initialised Nova SDS-011 sensor"}}'.format(sensor_id,get_local_timestamp()), 1)
    time.sleep(10)
  except:
    print("Nova SDS-011 sensor failed to initialise - bailing out!")
    myClient.publishAsync("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"failed to initialise Nova SDS-011 sensor"}}'.format(sensor_id,get_local_timestamp()), 1)
    time.sleep(30)
    sys.exit(1)
else:
  # if it gets to here, then an invalid particle sensor type was specified on the
  # command line, so might as well just exit, but sleep for 10 minutes first because
  # this program will automatically be restarted and the same error will happen until
  # it is fixed. A 10 minute wait stops too many error info messages being sent.
  print("invalid particulate sensor type specified on command line, shutting down in 10 minutes")
  myClient.publishAsync("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"invalid particulate sensor type specified on command line, shutting down in 10 minutes"}}'.format(sensor_id,get_local_timestamp()), 1)
  time.sleep(600)
  sys.exit(1)

##################################################
# set up BMP180 temp and air pressure sensor
##################################################

myClient.publishAsync("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"initialising BMP180 sensor"}}'.format(sensor_id,get_local_timestamp()), 1)
time.sleep(10)
try:
  # ultra-high res mode seems to work fine
  bmp = BMP085.BMP085(mode=BMP085.BMP085_ULTRAHIGHRES)
  print("BMP180 sensor initialised")
  myClient.publishAsync("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"initialised BMP180 sensor"}}'.format(sensor_id,get_local_timestamp()), 1)
  time.sleep(10)
except:
  print("BMP180 sensor failed to initialise, exiting program")
  myClient.publishAsync("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"BMP180 sensor failed to initialise, exiting program"}}'.format(sensor_id,get_local_timestamp()), 1)
  time.sleep(30)
  sys.exit(1)

# note: the DHT22 temp and humidity sensor doesn't require any set up

##################################################
# main loop forever
##################################################
print("Starting main loop")
myClient.publishAsync("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"starting main loop"}}'.format(sensor_id,get_local_timestamp()), 1)
time.sleep(10)

# initialise a main loop counter just for information
mainLoopCounter = -1

while True:

  # increment and display main loop counter
  mainLoopCounter += 1
  print("Main loop number {:d}".format(mainLoopCounter))

  # the idea is to take 20 readings at 15 second intervals from each sensor type and store the results
  # for each sensor type in a list, and then sort that list of values and discard the lowest three and highest
  # three readings, then calculate the average of the remaining readings. This is called a trimmed mean.
  # The trimmedMean() function defined above does this. This should get rid of most erroneous
  # measurements caused by sensor glitches will be discarded, and the data will be a lot cleaner
  # without spikes of obviously incorrect readings. This data cleaning could be done after the
  # data have been collected into the central database, but might as well do it at the
  # point of data collection on each sensor device.

  # first set up lists to hold the readings for each sensor device type on attached
  humidityReadings = list() # from the DHT22 sensor device
  temperatureReadings = list() # from the DHT22 device
  temperatureBmp180Readings = list() # from the BMP180 device
  airpressureReadings = list() # from the BMP180 device
  pm10Readings = list() # air particulates from either SDS-011 or Honeywell devices
  pm25Readings = list() # air particulates from either SDS-011 or Honeywell devices

  # now loop for 20 times to take readings from each device and append the reading to the
  # lists set up above
  # print loop counter on console for information
  # end='' stops a new line being added by print()
  print("Inner loop number: ", end='', flush=True)
  for t in range(20):

    print("{:d} ".format(t), end='', flush=True)

    # first get humidity and temp from the DHT22 device
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 17)
    # sometimes the DHT22 glitches and returns None as the readings, so check for that and
    # try again a few times, and send a message to the sensors/info MQTT topic stream
    if humidity is None or temperature is None:
      for rereadTry in range(1,6):
        # log a message to the sensors/info MQTT topic
        myClient.publishAsync("sensors/info", '{{"sensor":{:s},"timestamp":"{:s}","info":"DHT22 reading failed, try number {:d}"}}'.format(sensor_id, get_local_timestamp(),rereadTry), 1)
        # re-try after a few seconds
        time.sleep(10)
        humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 17)
        if humidity is not None and temperature is not None:
          # break out of this retry loop
          break
    # if still a reading error, then the value will be None, but it should be eliminated by
    # the trimmed means procedure
    # add the readings to the lists
    humidityReadings.append(float(humidity))
    temperatureReadings.append(float(temperature))

    # now read the BMP180 sensor. Check values and re-read if it returns None values
    # although it doesn't seem to
    bmp180_temperature = bmp.read_temperature()
    bmp180_airpressure = bmp.read_pressure()
    if bmp180_temperature is None or bmp180_airpressure is None:
      for rereadTry in range(1,6):
        # log a message to the sensors/info MQTT topic
        myClient.publishAsync("sensors/info", '{{"sensor":{:s},"timestamp":"{:s}","info":"BMP180 reading failed, try number {:d}"}}'.format(sensor_id, get_local_timestamp(),rereadTry), 1)
        # re-try after a few seconds
        time.sleep(10)
        bmp180_temperature = bmp.read_temperature()
        bmp180_airpressure = bmp.read_pressure()
        if bmp180_temperature is not None and bmp180_airpressure is not None:
          # break out of this retry loop
          break
    # if still a reading error, then the value will be None, but it should be eliminated by
    # the trimmed means procedure
    # add the readings to the lists
    airpressureReadings.append(float(bmp180_airpressure))
    temperatureBmp180Readings.append(float(bmp180_temperature))

    # finally read the particulate sensor device, using the correct driver for that device 
    if particulate_sensor_type == 'SDS011':
      # read the Nova SDS-011 sensor
      pm10, pm25 = sds.query()
    elif particulate_sensor_type == 'Honeywell':
      # read the Honeywell sensor, note that it also returns a timestamp but in UTC (Greenwich) time which we don't use
      pm_ts_utc, pm10, pm25 = str(hw.read()).split(",")
    else:
      # The particulate device type parameter on the command line must not be correct, so log it
      myClient.publishAsync("sensors/info", '{{"sensor":{:s},"timestamp":"{:s}","info":"particulate device type parameter incorrect!"}}'.format(sensor_id, get_local_timestamp()), 1)
      # sleep for 10 minutes since this error will keep happening until it is fixed
      time.sleep(600)
    # add the readings to the lists
    pm10Readings.append(float(pm10))
    pm25Readings.append(float(pm25))

    # now sleep for 10 seconds before repeating inner loop
    time.sleep(10)

  # go to a new line in the console output
  print(" ", flush=True)

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
  # send the data message, ask for an acknowledgement and call the acknowledge function to display this
  myClient.publishAsync("sensors/data", payload, 1, ackCallback=myPubackCallback)

  # sleep for a few seconds before starting all over again
  time.sleep(10)
