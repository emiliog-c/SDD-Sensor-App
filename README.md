# SDD-Sensor-App
sorted ou
This project is a full suite regarding the use of a Honeywell Particle sensor attached to a Raspberry Pi, for the use of detecting discrepensies in the air and also monitor temperature and humidity. THis package also connects to the internet, and sends all the data to a database for it to be placed into tables and exported to a website.

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
