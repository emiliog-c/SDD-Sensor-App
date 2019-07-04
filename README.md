# SDD-Sensor-App
sorted ou
This project is a full suite regarding the use of a Honeywell Particle or Nova SDS-011 sensor attached to a Raspberry Pi, for the use of detecting the level of dust and smoke particles in the air. 
There is also monitor temperature, humidity and air pressure through the Adafruit DHT22 sensor (add reference) and Adafruit BMP180.
The particle sensor communicate with the Raspberry Pi through the serial port on pins 2 (5V In), 8 (Recieved IN to transmit), 9 (GND IN) and 10 (Transmit IN to recieve).
The Adafruit DHT is connected on pins 1 (3.3V), 11 (GPIO17) and 14 (GND). There is a 7.5 kiloohm pullup resistor between the GPIO pin and 3.3V supply (see as per wiring diagram).
THe BMP180 air pressure sensor connects via I2C protocol (high speed serial protocol). Follow the instructions on this page to ensure that your sensor is working.
Pins 8 and 9 implement the serial port (UART) on the RPi.
This package also connects to the internet, and sends all the data to a database for it to be placed into tables and exported to a website.





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
Install required python libraries with the command (sudo pip3 install #)
# = AWSIoTPythonSDK
    adafruit-bmp
    Adafruit_DHT
Install the scripts using git clone https:/github.com/emiliog-c/SDD-Sensor-App.git
Change your directory using cd SDD-Sensor-App/rpi-sensor-node/
Type in sudo cp copy sensor1.boot.service /etc/systemd/system/
Test the startup with sudo systemctl start sensor1boot.service
Check startup with sudo systemctl status sensor1boot.service
Wait for 10 minutes, checking for appropriate messages and errors.
If all ok, enable script for automatic start at bootup with sudo systemctl enable sensor1boot.service



    

  



  



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


