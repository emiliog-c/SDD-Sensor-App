# SDD-Sensor-App
sorted ou
This project is a full suite regarding the use of a Honeywell Particle or Nova SDS-011 sensor attached to a Raspberry Pi, for the use of detecting the level of dust and smoke particles in the air. 
There is also monitor temperature, humidity and air pressure through the Adafruit DHT22 sensor (add reference) and Adafruit BMP180.
The particle sensor communicate with the Raspberry Pi through the serial port on pins 2 (5V In), 8 (Recieved IN to transmit), 9 (GND IN) and 10 (Transmit IN to recieve).
The Adafruit DHT is connected on pins 1 (3.3V), 11 (GPIO17) and 14 (GND). There is a 7.5 kiloohm pullup resistor between the GPIO pin and 3.3V supply (see as per wiring diagram).
THe BMP180 air pressure sensor connects via I2C protocol (high speed serial protocol). Follow the instructions on this page to ensure that your sensor is working.
Pins 8 and 9 implement the serial port (UART) on the RPi.
This package also connects to the internet, and sends all the data to a database for it to be placed into tables and exported to a website.


AWS Setup
Obtain AWS account 
Login to AWS console
Go to IoT-Core service
Click on onboard
Click on Get Started and continue
Choose the software package for Linux and the SDK for Python
Give your device the name of Sensor# (eg. Sensor1)
AWS automatically sets up Public and private access keys and client certificate (these need to be installed onto the sensor node so it can authenticate itself to the AWS service).
Download the software kit provided
At this point proceed to RPi Setup



Setup Procedure
Format SD Card (16GB)
Download latest NOOBS Distribution for RPi.
Connect RPi to HDMI Monitor and keyboard/mouse.
Boot RPi and choose raspberian install.
Wait for install and choose update all software.
From startup menu, complete; 
  Setup country/language
  Setup wifi
  Setup Password
From the config menu in the GUI, configure;
  Set Hostname (Sensor#)
  Enable SSH login
  Enable Serial port access
  Disable console over serial port (inteferes with dust sensor)
  Enable I2C
  Boot from console
Shutdown and reboot from console. It will now be accessible over WiFi through SSH.
You can remove all components excluding the power cord.
Login into the RPi via SSH protocol (i.e. PuTTy)
Login with pi and password given.
On your home computer, start cmd from the search bar and connect to the RPi pscp connect_device_package.zip pi@sensor#.local:/home/pi
In home directory, unzip connect_device_package.zip (places root and device certificate and the public and private key in the directories)
Install required python libraries with the command (sudo pip3 install #)
# = AWSIoTPythonSDK
    adafruit-bmp
    Adafruit_DHT
Return to the AWS home screen, and click on your sensor thing.
Navigate to interact, and copy the HTTPS address
Install the scripts using git clone https:/github.com/emiliog-c/SDD-Sensor-App.git
Change your directory using cd SDD-Sensor-App/rpi-sensor-node/
Type in nano sensor1boot.service (copy whole service file)
Change the sensor number to the number you are using
Paste in URL that you copied
Change the file names in the command line arguement to the correct names (i.e. /home/pi/Sensor#.private.key)
Change the type of sensor in the last part of the argument from either Honeywell or SDS011
Return to AWS command screen
Go to your sensor management
Click security, then the certificate
CLick policies and the policy given
Copy this into the policy document
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iot:Publish",
        "iot:Receive"
      ],
      "Resource": [
        "arn:aws:iot:ap-southeast-2:278221558381:topic/sdk/test/java",
        "arn:aws:iot:ap-southeast-2:278221558381:topic/sdk/test/Python",
        "arn:aws:iot:ap-southeast-2:278221558381:topic/sensors/data",
        "arn:aws:iot:ap-southeast-2:278221558381:topic/sensors/info"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Subscribe"
      ],
      "Resource": [
        "arn:aws:iot:ap-southeast-2:278221558381:topicfilter/sdk/test/java",
        "arn:aws:iot:ap-southeast-2:278221558381:topicfilter/sdk/test/Python",
        "arn:aws:iot:ap-southeast-2:278221558381:topicfilter/sensors/data",
        "arn:aws:iot:ap-southeast-2:278221558381:topicfilter/sensors/info"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Connect"
      ],
      "Resource": [
        "arn:aws:iot:ap-southeast-2:278221558381:client/Sensor1RPiZeroW",
        "arn:aws:iot:ap-southeast-2:278221558381:client/Sensor2RPiZeroW",
        "arn:aws:iot:ap-southeast-2:278221558381:client/Sensor3RPiZeroW",
        "arn:aws:iot:ap-southeast-2:278221558381:client/Sensor4RPiZeroW"
      ]
    }
  ]
}
Type in sudo cp copy sensor1boot.service /etc/systemd/system/
Test the startup with sudo systemctl start sensor1boot.service
Check startup with sudo systemctl status sensor1boot.service
Wait for 10 minutes, checking for appropriate messages and errors.
If all ok, enable script for automatic start at bootup with sudo systemctl enable sensor1boot.service
Repeat all steps for all nodes.
Click services and type in DynamoDB
Create a table with these table names
  Table name:	SDD-Sensors-Data
  Primary partition key:	sensorID (String)
  Primary sort key:	timestamp (String)
  Everything Default
Return to IoT Core console
Click on Act
Create two new rules
Give the rules a name, one to insert data into the table and the other to insert info messages into the table (log)
Copy this into the SQL Statement for the info table
  SELECT * FROM 'sensors/info'
Copy this into the SQL Statement for the data table
  SELECT * FROM 'sensors/data'
Add the action of inserting into a DynamoDB Table
Configure the actions according to this picture
Create a role in the action

The RPi node connects to the AWS IoT Services using the MQTT protocol (https://en.wikipedia.org/wiki/MQTT). MQTT is a protocol specifically designed for sending and recieving messages to and from Internet of things devices to a central server. It works on a publish and subscribe model, so to publish amessage, you have to specifically publish to the topic, and if you want to recieve a message, you have to subscribe to the topic. For simplicities sake, the node only publishes to two topics. Each node connects to the AWS MQTT server, the ode collects readings from the sensors attached to it, once it has looped 20 times, it will take an average and packages it into a JSON string and publishes it to the sensor.data topic on the AWS server. the AWS IoT MQTT library handles the message in the background, sending it directly to the server, automatically queuing messages if the internet goes down.WHen the topics recieves the data from the nodes, it applies the rules that were given to the topics and inserts the JSON data into the DynamoDB tables. 




    

  



  



Wires on the Honeywell Particle Sensor
Red = 5V
Black = GND
Yellow = Recieve
Blue = Transmit

Red Must be wired into 5V
Black Muste be wired into GND (ground)
Yellow Must be wired into Transmit
Blue must be wired to recieve

Red is soldered onto Pin 2 (5V)
Black is soldered onto Pin 6 (GND)
Yellow is soldered onto Pin 8 (Transmit)
Blue is soldered onto Pin 10 (Recieve)

Wires on the Adafruit DHT22 

Pin 1 = 3.3 Volt (Pin 1)
Pin 2 = GPIO4 (Pin 7)
Pin 3 = GND (Pin 8)


