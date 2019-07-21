"""
name: aboutApp.py
author: Emilio Guevarra Churches
date: July 2019
license: see LICENSE file
description: this is the code that creates the About tab in the app. It is imported by the main program.
"""

##################################################
# set-up section
##################################################

# import dash and dash bootstrap libraries needed
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc

##################################################
# function to build the about tab content
##################################################
# this function gets called from the main program to provide content for the About tab
def aboutApp():
    # make a Card for each of the sensor photos
    photo1 = dbc.Card([
        		dbc.CardImg(src="/assets/SDD-sensor1-node-photo1.png", top=True),
        		dbc.CardBody(
            		html.P("Sensor node 1 with Honeywell particulate sensor", className="card-text"))
        	 ])
    photo2 = dbc.Card([
        		dbc.CardImg(src="/assets/SDD-sensor1-node-photo2.png", top=True),
        		dbc.CardBody(
            		html.P("Sensor node 1 (side view)", className="card-text"))
        	 ])
    photo3 = dbc.Card([
        		dbc.CardImg(src="/assets/SDD-sensor4-node-photo1.png", top=True),
        		dbc.CardBody(
            		html.P("Sensor node 4 with Nova SDS-011 particulate sensor", className="card-text"))
        	 ])
    # and a Card for the overall diagram
    sensorDiagram = dbc.Card([
                dbc.CardImg(src="/assets/sensorDiagram.png", top=True),
                dbc.CardBody(
                    html.P("Diagram of how the overall system works.", className="card-text"))
        	 ])
    # put the sensor photos side by side in a Row
    sensorPhotos = dbc.Row([dbc.Col(photo1, width="4"),
					  dbc.Col(photo2, width="4"),
					  dbc.Col(photo3, width="4"),
			 ])
    # put the diagram in its own Row, in the middle between empty columns         
    sDiagram = dbc.Row([dbc.Col(width='2'),
                        dbc.Col(sensorDiagram, width="8"),
                        dbc.Col(width='2')
                    ],
                    align = 'center'
                    )
    # assemble the content inside another Card
    a = dbc.Card(body = True, children=[
				html.H4("About this app", className='card-title'),
            	html.H6("Written by Emilio Guevarra Churches", className='card-subtitle'),
                html.P(),
                html.P("This website shows all the information that is being supplied by multiple Raspberry Pi Sensors in different locations."),
                # use markdown text to embed links to other wen sites
                dcc.Markdown([
                		'''The Raspberry Pis are equipped with [Honeywell Particle Sensors](http://www.farnell.com/datasheets/2313714.pdf), capable of measuring PM2.5 and PM10 particles.
                		It is also equipped with an [Adafruit DHT22 temperature sensor](https://learn.adafruit.com/dht) and a [BMP180 air pressure sensor](https://tutorials-raspberrypi.com/raspberry-pi-and-i2c-air-pressure-sensor-bmp180/). 
                        More information can be found at the [Github page for this project](https://github.com/emiliog-c/SDD-Sensor-App).''']),
                html.P("All code regarding the creation of this project is written in Python, and the libraries Dash, plotly, dash-Bootstrap, the sensors' respective libraries, Amazon IoT libraries, Pandas, Boto3 and DynamoDB.",
                		className="card-text"),
                sDiagram,
                html.P(),
            	sensorPhotos,
        	])
    # return the about tab content
    return a
        
