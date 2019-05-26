from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import Adafruit_DHT
import honeywell
import time

# A random programmatic shadow client ID.
SHADOW_CLIENT = "Sensor1RPiZeroW"

# The unique hostname that AWS IoT generated for 
# this device.
HOST_NAME = "a3n039lf58a27m-ats.iot.ap-southeast-2.amazonaws.com"

# The relative path to the correct root CA file for AWS IoT, 
# that you have already saved onto this device.
# ROOT_CA = "AmazonRootCA1.pem"
ROOT_CA = "/home/pi/root-CA.crt"

# The relative path to your private key file that 
# AWS IoT generated for this device, that you 
# have already saved onto this device.
PRIVATE_KEY = "/home/pi/Sensor1.private.key"

# The relative path to your certificate file that 
# AWS IoT generated for this device, that you 
# have already saved onto this device.
CERT_FILE = "/home/pi/Sensor1.cert.pem"

# A programmatic shadow handler name prefix.
SHADOW_HANDLER = "Sensor1RPi"

# Automatically called whenever the shadow is updated.
def myShadowUpdateCallback(payload, responseStatus, token):
  print()
  print('UPDATE: $aws/things/' + SHADOW_HANDLER +
    '/shadow/update/#')
  print("payload = " + payload)
  print("responseStatus = " + responseStatus)
  print("token = " + token)

# Create, configure, and connect a shadow client.
myClient = AWSIoTMQTTClient(SHADOW_CLIENT)
myClient.configureEndpoint(HOST_NAME, 8883)
myClient.configureCredentials(ROOT_CA, PRIVATE_KEY,
  CERT_FILE)
myClient.configureConnectDisconnectTimeout(20)
myClient.configureMQTTOperationTimeout(10)
myClient.connect()
myClient.publish("sensors/info", '{"sensor":1, "info":"connected"}', 0)

# Create a programmatic representation of the shadow.
# myDeviceShadow = myShadowClient.createShadowHandlerWithName(
#  SHADOW_HANDLER, True)

# Represents the GPIO21 pin on the Raspberry Pi.
# channel = 21

# Use the GPIO BCM pin numbering scheme.
# GPIO.setmode(GPIO.BCM)

# Receive input signals through the pin.
# GPIO.setup(channel, GPIO.IN)

# setup Honeywell sensor
myClient.publish("sensors/info", '{"sensor":1, "info":"initialising Honeywell sensor"}', 0)
hw = honeywell.Honeywell()
#print("Wait 15 seconds...")
#time.sleep(15)
#print("Stop measuring")
#hw.stop_measuring()
#print("Wait 15 seconds...")
#time.sleep(15)
myClient.publish("sensors/info", '{"sensor":1, "info":"starting particulate measurements"}', 0)
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
#print("Take a reading...")
#while True:
#    reading = hw.read()
#    print(reading)
#    time.sleep(5)

while True:
  humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 17)
  if humidity is None or temperature is None:
    myClient.publish("sensors/info", '{"sensor":1, "info":"DHT22 reading failed"}', 0)
    # re-try after a few seconds
    time.sleep(5)
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 17)
    if humidity is None or temperature is None:
      myClient.publish("sensors/info", '{"sensor":1, "info":"DHT22 reading also failed on 1st retry"}', 0)
      # re-try after a few seconds
      time.sleep(5)
      humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 17)
      if humidity is None or temperature is None:
        myClient.publish("sensors/info", '{"sensor":1, "info":"DHT22 reading failed again on 2nd retry"}', 0)
  pm_ts, pm10, pm25 = str(hw.read()).split(",")
  print(humidity, temperature, pm_ts, pm25, pm10)
  if True:
     myClient.publish("sensors/data",
       '{{"sensor":"1","timestamp":"{:s}","temperature":{:f},"humidity":{:f},"pm25":{:d},"pm10":{:d}}}'.format(pm_ts,temperature, humidity,int(pm25),int(pm10)), 0)
      # myShadowUpdateCallback, 5)
     #myClient.publish("Sensor1/data",
     #  '{{"state":{{"reported":{{"humidity":{:f}}}}}}}'.format(humidity), 0)
      # myShadowUpdateCallback, 5)

  # Wait for this test value to be added.
  time.sleep(15)

