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
  return( sum(trimmedLst) / len(trimmedLst) )

# A programmatic client handler name prefix required by the AWS IoT MQTT client 
MQTT_HANDLER = "Sensor{:s}RPi".format(sensor_id)

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
myClient.configureConnectDisconnectTimeout(20)
myClient.configureMQTTOperationTimeout(20)
myClient.configureAutoReconnectBackoffTime(1, 128, 20)
myClient.configureOfflinePublishQueueing(20, AWSIoTPyMQTT.DROP_OLDEST)
myClient.configureDrainingFrequency(1)
# tell the client to connect with AWS
# use 2400 seconds for the keep-alive which is much longer than the 
# time between data sends, so the connection doesn't drop between
# each data send (publish)
myClient.connect(2400)
# seems to need a few seconds before the connection is ready to use
time.sleep(10)
# send a message to the sensors/info topic data stream saying that this sensor node
# has connected. The payload of the message is formatted as JSON with values for
# the sensor ID, the current date and time, and an information message as text
myClient.publish("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"MQTT client connected"}}'.format(sensor_id,get_local_timestamp()), 1)
time.sleep(10)

##################################################
# set up particulate sensor device
##################################################

# import the right library for the particulate sensor type for this node
if particulate_sensor_type == 'Honeywell':
  # the Honeywell driver already has serial port values set as required 
  import honeywell
  # set up Honeywell sensor
  # send an info message saying it is being initialised
  myClient.publish("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"initialising Honeywell sensor"}}'.format(sensor_id,get_local_timestamp()), 1)
  time.sleep(10)
  # create an instance of the Honeywell driver class
  hw = honeywell.Honeywell()
  # the Honeywell sensor also has to be told to start taking measurements
  myClient.publish("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"starting Honeywell particulate measurements"}}'.format(sensor_id,get_local_timestamp()), 1)
  time.sleep(10)
  hw.start_measuring()
elif particulate_sensor_type == 'SDS011':
  from sds011 import SDS011
  # the SDS-011 driver needs various serial port values to be set as constants
  DEFAULT_SERIAL_PORT = "/dev/serial0" # Serial port to use if no other specified
  DEFAULT_BAUD_RATE = 9600 # Serial baud rate to use if no other specified
  DEFAULT_SERIAL_TIMEOUT = 2 # Serial timeout to use if not specified
  DEFAULT_READ_TIMEOUT = 1 # How long to sit looking for the correct character sequence.
  # set up Nova SDS-011 sensor
  # send an info message saying it is being initialised
  myClient.publish("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"initialising Nova SDS-011 sensor"}}'.format(sensor_id,get_local_timestamp()), 1)
  time.sleep(10)
  # create an instance of the SDS011 driver class
  sds = SDS011(DEFAULT_SERIAL_PORT, use_query_mode=True)
else:
  # if it gets to here, then an invalid particle sensor type was specified on the 
  # command line, so might as well just exit, but sleep for 10 minutes first because
  # this program will automatically be restarted and the same error will happen until
  # it is fixed. A 10 minute wait stops too many error info messages being sent. 
  myClient.publish("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"invalid particulate sensor type, shutting down"}}'.format(sensor_id,get_local_timestamp()), 1)
  time.sleep(10)
  sys.exit(1)

##################################################
# set up BMP180 temp and air pressure sensor
##################################################

myClient.publish("sensors/info", '{{"sensor":"{:s}","timestamp":"{:s}","info":"initialising BMP180 sensor"}}'.format(sensor_id,get_local_timestamp()), 1)
time.sleep(10)
# ultra-high res mode seems to work fine
bmp = BMP085.BMP085(mode=BMP085.BMP085_ULTRAHIGHRES) 

# note: the DHT22 temp and humidity sensor doesn't require any set up

##################################################
# main loop forever
##################################################
while True:
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
  # lists we just set up
  for t in range(20):

    # first get humidity and temp from the DHT22 device
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 17)
    # sometimes the DHT22 glitches and returns None as the readings, so check for that and
    # try again a few times, and send a message to the sensors/info MQTT topic stream
    if humidity is None or temperature is None:
      for rereadTry in range(1,6):
        # log a message to the sensors/info MQTT topic
        myClient.publish("sensors/info", '{{"sensor":{:s},"timestamp":"{:s}","info":"DHT22 reading failed, try number {:d}"}}'.format(sensor_id, get_local_timestamp(),rereadTry), 1)
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
        myClient.publish("sensors/info", '{{"sensor":{:s},"timestamp":"{:s}","info":"BMP180 reading failed, try number {:d}"}}'.format(sensor_id, get_local_timestamp(),rereadTry), 1)
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
      myClient.publish("sensors/info", '{{"sensor":{:s},"timestamp":"{:s}","info":"particulate device type parameter incorrect!"}}'.format(sensor_id, get_local_timestamp()), 1)
      # sleep for 10 minutes since this error will keep happening until it is fixed
      time.sleep(600)
    # add the readings to the lists
    pm10Readings.append(float(pm10))
    pm25Readings.append(float(pm25))

    # now sleep for 10 seconds before repeating inner loop
    time.sleep(10)

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
  if myClient.publish("sensors/data", payload, 1):
    print("Data payload message sent")
  else:
    print("Unable to publish payload, will try again next round")

  # sleep for a few seconds before starting all over again
  time.sleep(10)
