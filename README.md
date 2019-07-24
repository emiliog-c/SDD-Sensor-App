# SDD-Sensor-App

### by Emilio Guevarra Churches

## Overview

* This project creates an IoT (internet of things) full suite which uses a Honeywell or Nova SDS-011 smoke and dust sensor attached to one or more Raspberry Pi computers for the use of detecting the level of dust and smoke particles in the air. 
* There is also monitoring of temperature, humidity and air pressure through the Adafruit DHT22 sensor and Adafruit BMP180 sensor.
* Each Raspberry Pi with the above sensors attached is called a “sensor node”. The code for the web app for this project assumes there are 4 sensor nodes, but it is easy to modify the code if there are more or less than 4.
*	The sensor nodes run a python program that collects data from the sensors attached and packages it in [JSON format](https://json.org), and then sends that data to the [Amazon IoT service](https://aws.amazon.com/iot-core/) in the cloud via the [MQTT protocol](https://mqtt.org) which is used a lot for IoT communications.
*	The Amazon IoT service is set up to automatically send the data it receives from each sensor node in JSON format to a [Amazon DynamoDB database](https://aws.amazon.com/dynamodb/)
* A web app written in python using the [Dash framework](https://dash.plot.ly) for dashboards that display information  can then be run on a laptop and the web site it creates can be viewed in a web browser, or it can be deployed to a web server connected to the internet so that many people can access it. For this project [Amazon Elastic Beanstalk](https://aws.amazon.com/elasticbeanstalk/) was used to make a web server with just a few commands.

## Installation

Please see the [Installation Guide](docs/installation_guide_final.pdf).

## Use

Please see the [User Guide](docs/user_guide_final.pdf).
