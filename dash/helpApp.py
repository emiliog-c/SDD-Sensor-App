"""
name: helpApp.py
author: Emilio Guevarra Churches
date: July 2019
license: see LICENSE file
description: this is the code that creates the help tab in the app. It is imported by the main program.
"""

##################################################
# set-up section
##################################################
# import the dash libraries needed
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc

##################################################
# markdown text section
##################################################
# this is the text for the help tab in markdown format
# doing it like this is much easier than assembling it
# bit by bit as I did in the aboutApp.py file

markDownText = '''
### How to use this web app

Located at the top of the app page is the header. It contains the title of the project, 
a refresh button and a message stating when the data being displayed was last refreshed. 
The refresh button obtains the newest data from the database that the sensors send their 
data to and displays it in the homepage, graphs, and table views The tabs under the header 
display different views of the data, as well as the message log from the sensors and this 
help file and the about tab.

The homepage tab shows the most recent values that each sensor has supplied.

The graph view displays an assortment of time-series graphs for each type of sensor 
reading. The graphs show the various values over time which the sensors have accumulated. 
At the top of the graphs, there are preset time periods that you can select – the graphs 
will then display only that time period. Hovering your mouse pointer at any point of the 
graph will show the sensors ID number and the values it had at that moment in time. At the 
bottom is a custom scale option that can narrow down the time period you desire to look at. 
Clicking on a time-series line or legend for each sensor on the side will remove it from 
the graph, while double-clicking it will isolate it in the graph.

At the top-right of each time-series graph there are a series of icons that allow you to 
do things like download the graph as a PNG file, zoom in or out, pan the graph sideways, 
and compare data points on the graph. Hovering your mouse pointer above each icon shows 
what it does.

The data and log view are tables that show the raw data that the sensors collect and the 
status of the sensors respectively. Clicking the headers at the top of each column in the 
tables will sort the data by the values in that column, in either descending, or by 
clicking again, ascending order. If you enter values under the header for each column, 
the table will automatically be filtered to show just those values. You can also use 
comparisons such as < or > (less than or greater than).

-----

### General Questions

**Q**: Is it safe for the sensor node just to be turned off?
* **A:** In general, yes. Ideally the sensor should be shut down using a linux command before the power is removed, but in practice it should survive just having the power turned off OK.


**Q**: If the sensor disconnects from the internet due to an outage, will it reconnect 
and what will happen to the data collected when it was offline?
* **A**: It should automatically reconnect, and the data will have been stored locally until it can be sent to the cloud, which it will do automatically when it reconnects.


**Q**: How do I know if the sensor is down?
* **A**: Inspect the home page of the dash app to see when the sensor last sent data. The Log View tab can be used to see if there are any log messages from the sensor which might indicate what is wrong, although if the wi-fi connection for the sensor is down, then log messages cannot be sent either.
>

**Q**: If I want to assign a sensor to a new DynamoDB table, how would I do that?
* **A**: Follow the installation guide regarding the setup of the DynamoDB table.

**Q**: What do I need to run this sensor?
* **A**: Python version 3.6 or later, the libraries that need to be installed detailed in the installation guide, an Amazon Web Services account and a working internet connection.

**Q**: What's the difference between the sensor_run.py file and the sensorDashApp.py file?
* **A**: The sensor_run.py file runs the sensors on the sensor Raspberry Pi devices and sends all the information via MQTT to the DynamoDB tables made with AWS services. The sensorDashApp.py file takes the data from the DynamoDB tables, places it in graphs and presents it as a website.

-----

### Troubleshooting and customisation

#### The Application is loading extremely slowly

**Reason**: When the application loads up, it loads all the data from the DynamoDB table, causing slow loads as the applications tables and graphs will not load until all of the data is loaded.

** Resolution**: Remove data from the DynamoDB table to decrease loading time, or change the number of times the program sends information (to do that, locate the sensor_run.py file, go down to line 210, and change the value of the time.sleep() to however many seconds you want the sensor to wait until it takes the next measurement).

Every few months it may be necessary to delete older data to keep the data size manageable. This has to be done using program code at the moment. A useful enhancement would be to make such deletion of older data automatic.

#### The application gives many errors at bootup

**Reason**: If you are running the web site on your laptop, you may not have all the required libraries for the Python program to run, causing a multitude of errors as it cannot display any graphs and tables due to the code that is unknown to Python as it does not have the required libraries.

**Resolution**: Open up your respective OS’ console (Window’s CMD, Mac’s Terminal), and type pip3 install plus the name of the respective libraries shown in the installation file. Rerun the Dash App file from your command terminal.

#### The Sensors are not sending information to the DynamoDB tables

**Reason**: You may not have your policies setup properly or the certificates are not properly placed in the boot files.

**Resolution**: Inspect your policies in the security section of the Amazon Web Services IoT, ensuring that your policies are set. Inspect your boot files, ensuring that the certificate numbers are properly placed.
'''

##################################################
# function to create the help tab content
##################################################
# this gets called in the main program to create the content of the help tab
def helpApp():
	a = dbc.Card(body = True, children=[
                	dcc.Markdown([markDownText],className="card-text"),
        		])          
	return a
        
