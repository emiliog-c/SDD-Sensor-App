"""
name: sensorDashApp.py
author: Emilio Guevarra Churches
date: July 2019
license: see LICENSE file
description: this is the main web app file. it can be run on your laptop or on a web server.
"""

##################################################
# set-up section
##################################################

import boto3 # Amazon AWS SDK library for access DynamoDB database
from boto3.dynamodb.conditions import Key, Attr # used in filtering queries
import json # library to deal with JSON data
import time
from datetime import datetime
from decimal import Decimal # used to deal with DynamoDB representations of decimals
from dynamodb_json import json_util as json # used to convert DynamoDB JSON to normal JSON
import pandas as pd # pandas library for manipulating data
from pandas.io.json import json_normalize # un-nests (flattens) nested JSON data as required by pandas
import dash # main dash framework for dashboard web app
import dash_auth # dash authentication library
from aboutApp import aboutApp # function to build About tab content
from helpApp import helpApp # function to build help tab content
from app_passwords import VALID_USERNAME_PASSWORD_PAIRS # usernames and passwords
# note: the app_passwords.py file imported in the line above
# just contains something like this:
# # Keep this out of git and GitHub!
# VALID_USERNAME_PASSWORD_PAIRS = {
#    'admin': 'XXXX',
#     'sensor1': 'XXXX',
#     'sensor2': 'XXXXX',
#     'sensor3': 'XXXXX',
#     'sensor4': 'XXXXX',
# }
# where XXXX is the password for each user
import dash_table # library to create tables in dash
import dash_daq as daq # library of extra dash widgets like thermometer and guages
import dash_core_components as dcc # core dash components
import dash_bootstrap_components as dbc # Bootstrap libraries as extensions to dash
import dash_html_components as html # dash HTML components
from dash.dependencies import Input, Output # needed for callback from Refresh button
from dash_table.Format import Format, Scheme, Sign, Symbol # used to format the tables
import plotly.plotly as py # main graph library used in dash
import plotly.graph_objs as go
import sys
import platform # needed to work out which operating system

##################################################
# get data from DynamoDB database section
##################################################

# create an AWS session which references the .aws/credentials file in home directory
# the credentials file has a section called SDD-Sensors containing the AWS account 
# identifier and secrete key (passowrd) for it to access the DynamoDB database
if platform.system() == 'Windows' or platform.system() == 'Darwin':
    session = boto3.Session(profile_name='SDD-Sensors')
else:
    # if linux then will check environment variables automatically, if says
    session = boto3.Session()

# set up a handle to the database
dynamodb = session.resource('dynamodb', region_name='ap-southeast-2',)
# set up handles for the two tables: one for sensor data, one for information messages from the sensors
dataTable = dynamodb.Table('SDD-Sensors-Data')
infoTable = dynamodb.Table('SDD-Sensors-Info')

# make a function to extract all the data into an in-memory Pandas dataframe
# dataTable.scan() scans and returns JSON containing every record in the database 
# in a JSON filed called "Items". We extract that field and process it with the 
# json.loads() method from the dynamodb_json library. This converts the DynamoDB format
# JSON into normal-looking JSON. Then we pass that through json_normalize() which
# flattens or un-nests the JSON (our actual sensor data is contained in a field called 
# "data", whereas we want it as a single flat row of data items. Finally, we
# process the flattened JSON data with the Pandas DataFrame() methods which
# returns a Pandas dataframe object.

def getSensorData(): 
    response = dataTable.scan()
    data = response['Items']
    # dynamoDb sends the data as pages so we need to loop until no more pages
    # this was just copied from the DynamoDb tutorial on AWS
    while response.get('LastEvaluatedKey'):
        response = dataTable.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
    
    # load data into a pandas DataFrame via the json.loads() function
    # that converts DynamoDB JSON into standard JSON (see https://github.com/Alonreznik/dynamodb-json )
    # and via the json_normalize() function in pandas that converts nested JSON data into a flat table form
    # required by pandas
    sensorData = pd.DataFrame(json_normalize(json.loads(data)))

    # first bit of tidying up is to delete the additional sensor ID column
    sensorData = sensorData.drop(columns="data.sensor")

    # now we need to convert the timestamp columns from strings into python datetime format
    # using the built-in Pandas to_datetime() method on those columns. In Pandas, columns
    # can be referenced just by using square brackets.
    sensorData['data.timestamp'] = pd.to_datetime(sensorData['data.timestamp'])
    sensorData['timestamp'] = pd.to_datetime(sensorData['timestamp'])
    # also convert the SensorID column from string into integer
    sensorData['sensorID'] = sensorData['sensorID'].astype('int64')
    # sort data set according to this https://www.geeksforgeeks.org/python-pandas-dataframe-sort_values-set-2/
    sensorData.sort_values(["timestamp", "sensorID"], axis=0, ascending=[False,True], inplace=True)
    # converts the air pressure into hPa
    sensorData['data.bmp180_airpressure'] = sensorData['data.bmp180_airpressure']/100.0
    # return the pandas dataframe
    return(sensorData)

# this functions the same as getSensorData, but reads from the SDD-Sensors-Info table in DynamoDB to
# supply the sensorInfo dataframe table in dash
def getSensorInfo():
    response = infoTable.scan()
    data = response['Items']
    while response.get('LastEvaluatedKey'):
        response = infoTable.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
    sensorInfo = pd.DataFrame(json_normalize(json.loads(data)))
    # sort data set according to this https://www.geeksforgeeks.org/python-pandas-dataframe-sort_values-set-2/
    sensorInfo.sort_values(["timestamp", "sensorID"], axis=0, ascending=[False,True], inplace=True)
    # also convert the SensorID column from string into integer
    sensorInfo['sensorID'] = sensorInfo['sensorID'].astype('int64')    
    return(sensorInfo)


##################################################
# set up the dash app
##################################################
# most of this code is based on the tutorials for the Dash library

# the stylesheets are needed by the Dash Bootstrap Components library
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# this is needed to run properly on AWS ElasticBeanstalk
application = app.server

#set up basic authentication as per https://dash.plot.ly/authentication
# doesn't work on Windows so skip it if running Windows
if platform.system() != 'Windows':
    auth = dash_auth.BasicAuth(
        app,
        VALID_USERNAME_PASSWORD_PAIRS
    )

##################################################
# Function to make the specifications in dictionaries for all the graphs 
# for later use in different functions.
# Code based on this blog post by chriddyp who wrote the dash library: 
# https://community.plot.ly/t/ploting-time-series-data/5265
# If you needing to change the graphs, change them here.
##################################################
def make_graph(sensorData, column, gtitle, y_label):
	sensor1 = dict(
		x=sensorData[sensorData.sensorID == 1].timestamp,
		y=sensorData[sensorData.sensorID == 1][column],
		name = "Sensor 1",
		line = dict(color = '#1f77b4'),
		opacity = 0.4)

	sensor2 = dict(
		x=sensorData[sensorData.sensorID == 2].timestamp,
		y=sensorData[sensorData.sensorID == 2][column],
		name = "Sensor 2",
		line = dict(color = '#d62728'),
		opacity = 0.4)

	sensor3 = dict(
		x=sensorData[sensorData.sensorID == 3].timestamp,
		y=sensorData[sensorData.sensorID == 3][column],
		name = "Sensor 3",
		line = dict(color = '#bcbd22'),
		opacity = 0.4)

	sensor4 = dict(
		x=sensorData[sensorData.sensorID == 4].timestamp,
		y=sensorData[sensorData.sensorID == 4][column],
		name = "Sensor 4",
		line = dict(color = '#fcbd22'),
		opacity = 0.4)

	data = [sensor1, sensor2, sensor3, sensor4]

	layout = go.Layout(
		title=gtitle,
		yaxis=dict(title = y_label),
		xaxis=dict(
			title = 'Date/time',
			rangeselector=dict(
				buttons=list([
					dict(count=30,
						 label='last 30 mins',
						 step='minute',
						 stepmode='backward'),
					dict(count=3,
						 label='last 3 hrs',
						 step='hour',
						 stepmode='backward'),
					dict(count=12,
						 label='last 12 hrs',
						 step='hour',
						 stepmode='backward'),
					dict(count=1,
						 label='last 24 hrs',
						 step='day',
						 stepmode='backward'),
					dict(count=3,
						 label='last 3 days',
						 step='day',
						 stepmode='backward'),
					dict(step='all')
				])
			),
			rangeslider=dict(
				visible = True
			),
			type='date',
			)
		)

	fig = {'data': data, 'layout': layout}
	return(fig)
    

##################################################
# creates graphs using the data from the DynamoDB Table. 
# Uses the graph specifications created by the make_graph() function above.
##################################################
def SensorGraph(sensorData):
    # style dictionary for each graph
    graphstyle = {'width': '70vw', 'display': 'block', 'margin-left': 'auto', 'margin-right': 'auto'}
    # cards are part of bootstrap, makes laying out extremely easily. The card also creates a border around each graph.
    # Inside each card the graph is created by the dash Graph() function that makes a Plotly graph
    graphdiv = dbc.Card(body=True, children=[
            dbc.Card(body = True, color='primary', outline=True, className='mt-2', 
            		children=[dcc.Graph(id='bmp180-temp-graph', style=graphstyle, 
            		figure=make_graph(sensorData, 'data.bmp180_temperature', 'Temperature (BMP180 sensor)', 'degrees Celcius'))]),
            dbc.Card(body = True, color='primary', outline=True, className='mt-2', 
            		children=[dcc.Graph(id='humidity-graph', style=graphstyle, 
            		figure=make_graph(sensorData, 'data.humidity', 'Humidity', '% relative humidity'))]),
            dbc.Card(body = True, color='primary', outline=True, className='mt-2', 
            		children=[dcc.Graph(id='bmp180-airpress-graph', style=graphstyle, 
            		figure=make_graph(sensorData, 'data.bmp180_airpressure', 'Air pressure', 'hectoPascals'))]),
            dbc.Card(body = True, color='primary', outline=True, className='mt-2', 
            		children=[dcc.Graph(id='pm25-graph', style=graphstyle, 
            		figure=make_graph(sensorData, 'data.pm25', 'PM 2.5', 'micrograms per cubic metre'))]),
            dbc.Card(body = True, color='primary', outline=True, className='mt-2', 
            		children=[dcc.Graph(id='pm10-graph', style=graphstyle, 
            		figure=make_graph(sensorData, 'data.pm10', 'PM 10', 'micrograms per cubic metre'))]),
            ])
    return graphdiv

##################################################
# creates a table that presents the info from the sensorInfo pandas dataframe
# (i.e. status of the sensors) which was loaded from the DynamoDB table. 
# Uses Dash DataTable library to create the table.
##################################################
def infoTableDisplay(sensorInfo):
    # mx-auto class supposed to centre the table on the page, but doesn't
    # seem to work when deployed to web server no idea why
    x = dbc.Card(body=True, className='mx-auto', children=[	
        dash_table.DataTable(id='sensor-info-table', 
        # Change the name value if you want to change the header of the column shown
        columns=[{'name': 'Sensor ID', 'id': 'sensorID','type': 'numeric'},
                    {'name': 'Timestamp', 'id': 'timestamp', 'type': 'datetime'},
                    {'name': 'Log message', 'id': 'info.info',
                     'type': 'text'}
		],
        # this makes the rows striped for easy reading, cribbed from Dash docs
        style_cell_conditional=[
            {
                'if': {'column_id': c},
                'textAlign': 'left'
            } for c in ['info.info', 'timestamp', 'sensorID']
        ],
        # needed to convert pandas data frame into format needed by Dash Datatable
	# as per the docs
        data=sensorInfo.to_dict('records'),
        # the rest of these are settings for the table as per the docs
        style_as_list_view=True,
        style_cell={'padding': '5px'},
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        editable=False,
        filter_action='native',		     
        sort_action='native',
        sort_mode="multi",
        row_selectable=False,
        row_deletable=False,
        selected_rows=[],
        page_size = 50         
        ),
        ])
    return(x)
    
##################################################
# Same as the code above, but presents the data frame which 
# contains the actual data directly from the sensors.
##################################################
    
def dataTableDisplay(sensorData):
    x = dbc.Card(body=True, className='mx-auto', children=[	
        dash_table.DataTable(id='sensor-data-table', 
        #Change the name value if you want to change the name of the table column
        columns=[{'name': 'Sensor ID', 'id': 'sensorID', 'type': 'numeric'},
                    {'name': 'Timestamp', 'id': 'timestamp', 'type': 'datetime'},
                    {'name': u'Temperature (˚C)', 
                     'id': 'data.temperature',
                     'type': 'numeric',
                     'format': Format(precision=1, scheme=Scheme.fixed)},
                    {'name': 'Rel. Humidity %', 
                     'id': 'data.humidity',
                     'type': 'numeric',
                     'format': Format(precision=1, scheme=Scheme.fixed)},
                    {'name': 'Air pressure (hPa)', 
                     'id': 'data.bmp180_airpressure',
                     'type': 'numeric',
                     'format': Format(precision=2, scheme=Scheme.fixed)},
                    {'name': 'PM2.5', 
                     'id': 'data.pm25',
                     'type': 'numeric',
                     'format': Format(precision=2, scheme=Scheme.fixed)},
                    {'name': 'PM10', 
                     'id': 'data.pm10',
                      'type': 'numeric',
                     'format': Format(precision=2, scheme=Scheme.fixed)},
                ],
        data=sensorData.to_dict('records'),
        style_as_list_view=True,
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ],
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
	editable=False,
	filter_action='native',
        sort_action='native',
	sort_mode="multi",
	row_selectable=False,
	row_deletable=False,
	selected_rows=[],
	page_size = 50,
        )
    ])
    return(x)
    
##################################################
# function to set up the homepage content
##################################################

def homepageDisplay(latestSensorData):
    # need to do this to get data for each sensor in the loop below
    df2 = latestSensorData.set_index('sensorID', drop = False)
    j = [] # this list holds section for each sensor
    # now loop for each sensor node
    # if more sensor nodes are available, change the range to sensorID + 1 
    # (i.e. if you have installed sensor 5, change the last number to 6
    for sID in range(1,5):
        #card creates a border around the sensors gauges
        k = [dbc.Card(body = True, color='primary', outline=True, className='mt-2', children=[    
                dbc.Row([
		    # show the sensor number and latest timestamp for this sensor
                    dbc.Col([
                        html.H4('Sensor {:d}'.format(sID)),
                        html.Div('Latest update'),
                        html.Div(df2.at[sID, 'timestamp'])],
                        width = 2,
                    ),
		    # show the temp in a thermometer
                    dbc.Col(
                        daq.Thermometer(
                        min=-10,
                        max=50,
                        value = df2.at[sID,'data.bmp180_temperature'],
                        scale={'start': -10, 'interval': 5},
                        showCurrentValue=True,
                        units="C"),
                        width = "auto",
                    ),
		    # show humidity in a gauge
                    dbc.Col(
                        daq.Gauge(
                        showCurrentValue=True,
                        units="Rel.Humidity%",
                        value=df2.at[sID,'data.humidity'],
                        label='Humidity',
                        max=100,
                        min=0,
                        size=200,),
                        width = "auto",
                    ),
		    # show air pressure in a gauge
                    dbc.Col(
                        daq.Gauge(
                        showCurrentValue=True,
                        units="Hectopascals (hPa)",
                        value=df2.at[sID,'data.bmp180_airpressure'],
                        label='Barometer',
                        max=1200,
                        min=800,
                        size=200,),
                        width = "auto",
                    ),
                    # uses two rows to have the displays right under each other while still being
		    # in the same row as the other gauges to show particulates reading as an LED display
                    dbc.Col([
                        dbc.Row(
                            daq.LEDDisplay(
                            label="PM2.5 (µg/m3)",
                            labelPosition='bottom',
                            backgroundColor="#5be4fc",
                            color="#000000",
                            value=df2.at[sID,'data.pm25'].round(2)),
                            ),
                        dbc.Row(
                            daq.LEDDisplay(
                            label="PM10 (µg/m3)",
                            labelPosition='bottom',
                            backgroundColor="#5be4fc",
                            color="#000000",
                            value=df2.at[sID,'data.pm10'].round(2)),
                            )
                            ],
                     width = "auto",
                     align = "center",
                     ), 
                ])]
            )
            ]
        j.extend(k) # add section for each sensor to overall list of sections
    l= html.Div(children=[
        dbc.Card(
            dbc.CardBody(j) # put all the sections inside another outer card
            )
        ])
    # return the overall homepage content
    return l
    
##################################################
# This is the overall app layout that defines the header bar that is present on all pages. 
# This facilitates the tabs and the data refresh button.
##################################################   
app.layout = html.Div(className='container', children=[
    dbc.Card(body=True, color='primary', inverse=True, className='m-2', children=[
                html.Div(id='header-div', children=[
                    dbc.Row([
			# overall app heading
                        dbc.Col(html.H1('SDD Sensor App Dashboard'),width=7, align='center'),
			# this is the pulsating data loading indicator
                        dbc.Col(dcc.Loading(id="loading-1", children=[html.Div(id="loading-output-1")], type="dot"), width=3, align='center'),
                        # Refresh button that is located on the header. Must be put in the header as the header 
                        dbc.Col(dbc.Button('Refresh', id='refresh-button', className = 'mr-1', color = "success", size='sm'), width=2, align='center'),
                    ])
                ]),
            ]),
    # now under the header place all the tabs
    dbc.Tabs(id="htmltabs", children=[
        dbc.Tab(id='Homepage', label='Homepage'),
        dbc.Tab(id = 'time-series-tab', label='Graph View'),
        dbc.Tab(id = 'data-table-tab', label='Data Table View'),
        dbc.Tab(id = 'log-messages-tab', label='Log View'),
        # These tabs rely on functions defined in external .py files 
	# which refer to photoes etc found in the assets directory in 
	# this folder, If you want to change the text, look in the helpApp.py and aboutApp.py file.
        dbc.Tab(id = 'help-tab', label='Help', children=helpApp()), 
        dbc.Tab(id = 'about-tab', label='About', children=aboutApp())
    ])])

# This callback sets the refresh button up for refreshing the tabs specifically.
# callbacks fire when you click the button 
# this is explained in https://dash.plot.ly/getting-started-part-2
# the output sections below tell each tab that involves data to reload the new data
# The callback specification has to be immediately above the definition of the function that 
# updates the data from the DynamoDb database
@app.callback([Output('Homepage', 'children'),
               Output('time-series-tab', 'children'),
               Output('log-messages-tab', 'children'),
               Output('data-table-tab', 'children'),
               Output('loading-output-1', 'children')
               ],
              [Input('refresh-button', 'n_clicks')]
              )
def updateData(n_clicks):
        sensorData = getSensorData()
        #Triggers when the refresh button is hit
        timeLastRefreshed = "Data was last refreshed at {:%H:%M:%S on %d %B, %Y}".format(datetime.now())
        sensorInfo = getSensorInfo()
        # updating last obtained data
        # This also refreshes the children of each tab instead of calling them in the header function
	# either way works, but this is faster
	# first we get the latest timestamp for each sensorID
        maxTimestamps = sensorData.groupby('sensorID')['timestamp'].max().reset_index() 
	# and we use that to get the row containing the latest data for each sensorID
        latestSensorData = pd.merge(sensorData, maxTimestamps, how='inner') 
	# now we rebuild the content for each tab using the updated data
        hp = homepageDisplay(latestSensorData)
        tsg = SensorGraph(sensorData)
        itd = infoTableDisplay(sensorInfo)
        dlt = dataTableDisplay(sensorData)
	# return all the chunks of content which are sent to each tab as per the Output specs
	# in the callback bit above
        return(hp, tsg, itd, dlt, timeLastRefreshed)

# finally, run the actual Dash web app
if __name__ == '__main__':
    app.run_server(debug=True)



