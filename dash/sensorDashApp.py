import boto3 # Amazon AWS SDK library for access DynamoDB database
from boto3.dynamodb.conditions import Key, Attr # used in filtering queries
import json # library to deal with JSON data
import time
from datetime import datetime
from decimal import Decimal # used to deal with DynamoDB representations of decimals
from dynamodb_json import json_util as json # used to convert DynamoDB JSON to normal JSON
import pandas as pd # pandas library for manipulating data
from pandas.io.json import json_normalize # un-nests (flattens) nested JSON data as required by pandas
import dash
import dash_auth
from aboutApp import aboutApp
from app_passwords import VALID_USERNAME_PASSWORD_PAIRS 
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
import dash_table
import dash_daq as daq
import pandas as pd
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash_table.Format import Format, Scheme, Sign, Symbol
import plotly.plotly as py
import plotly.graph_objs as go
import sys
import platform

# create an AWS session, references the .aws/credentials file in home directory
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

# print(dataTable.table_name)

# extract all the data into an in-memory Pandas dataframe
# dataTable.scan() scans and returns JSON containing every record in the database 
# in a JSON filed called "Items". We extract that field and process it with the 
# json.loads() method from the dynamodb_json library. This converts the DynamoDB format
# JSON into normal-looking JSON. Then we pass that through json_normalize() which
# flattens or un-nests the JSON (our actual sensor data is contained in a field called 
# "data", whereas we want it as a single flat row of data items. Finally, we
# process the flattened JSON data with the Pandas DataFrame() methods which
# returns a Pandas dataframe object.


n_clicks = 0

def getSensorData(): 
    response = dataTable.scan()
    data = response['Items']
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
        # can be referenced just using square brackets.
        sensorData['data.timestamp'] = pd.to_datetime(sensorData['data.timestamp'])
        sensorData['timestamp'] = pd.to_datetime(sensorData['timestamp'])
        # also convert the SensorID column from string into integer
        sensorData['sensorID'] = sensorData['sensorID'].astype('int64')
        # sort data set according to this https://www.geeksforgeeks.org/python-pandas-dataframe-sort_values-set-2/
        sensorData.sort_values(["timestamp", "sensorID"], axis=0, ascending=[False,True], inplace=True)
        sensorData['data.bmp180_airpressure'] = sensorData['data.bmp180_airpressure']/100.0

    return sensorData

sensorData = getSensorData()


# print out the dataframe
# print(sensorData)
# show info about the dataframe
print(sensorData.info())

# do the same for the sensors info table
def getSensorInfo():
    response = infoTable.scan()
    data = response['Items']
    while response.get('LastEvaluatedKey'):
        response = infoTable.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
    sensorInfo = pd.DataFrame(json_normalize(json.loads(data)))
    # sort data set according to this https://www.geeksforgeeks.org/python-pandas-dataframe-sort_values-set-2/
    sensorInfo.sort_values(["timestamp", "sensorID"], axis=0, ascending=[False,True], inplace=True) 
    return(sensorInfo)

# print out the dataframe
# print(sensorInfo)
# show info about the dataframe
# print(sensorInfo.info())

print(sensorData.groupby('sensorID').count())

# sys.exit()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# this is needed to run properly on AWS ElasticBeanstalk
application = app.server

#setup basic authentication as per https://dash.plot.ly/authentication
# doesn't work on Windows so skip it if running Windows
if platform.system() != 'Windows':
    auth = dash_auth.BasicAuth(
        app,
        VALID_USERNAME_PASSWORD_PAIRS
    )

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

def SensorGraph(sensorData):
    graphstyle = {'width': '70vw', 'display': 'block', 'margin-left': 'auto', 'margin-right': 'auto'}
    graphdiv = dbc.Card(body=True, children=[
            # don't need two temperature graphs
            # dbc.Card(body = True, color='primary', outline=True, className='mt-2', 
            # 		children=[dcc.Graph(id='temp-graph', style=graphstyle, 
            # 		figure=make_graph(sensorData, 'data.temperature', 'Temperature', 'degrees Celcius'))]),
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

def infoTableDisplay(sensorInfo):
    x = html.Div(children=[	
        dash_table.DataTable(id='sensor-info-table', 
        #columns=[{"name": i, "id": i} for i in sensorInfo.columns],
        columns=[{'name': 'Sensor ID', 'id': 'sensorID'},
                    {'name': 'Timestamp', 'id': 'timestamp', 'type': 'datetime'},
                    {'name': 'Log message', 'id': 'info.info',
                     'type': 'text'}
		],
        style_cell_conditional=[
            {
                'if': {'column_id': c},
                'textAlign': 'left'
            } for c in ['info.info', 'timestamp', 'sensorID']
        ],
        data=sensorInfo.to_dict('records'),
        style_as_list_view=True,
        style_cell={'padding': '5px'},
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
                editable=False,
                filter_action='native',		     
                # filtering=True,
                sort_action='native',
                #sort_mode="multi",
                row_selectable="multi",
                row_deletable=False,
                selected_rows=[],
                # pagination_mode="fe",
                # pagination_settings={
                #     "current_page": 0,
                #	    "page_size": 50}         
                ),
        ])
    return(x)
    
def dataTableDisplay(sensorData):
    x = html.Div(children=[	
        dash_table.DataTable(id='sensor-data-table', 
        columns=[{'name': 'Sensor ID', 'id': 'sensorID'},
                    {'name': 'Timestamp', 'id': 'timestamp', 'type': 'datetime'},
                    {'name': u'Temperature (˚C)', 
                     'id': 'data.temperature',
                     'type': 'numeric',
                     'format': Format(precision=1, scheme=Scheme.fixed)},
                    {'name': 'Rel. Humidity %', 
                     'id': 'data.humidity',
                     'type': 'numeric',
                     'format': Format(precision=1, scheme=Scheme.fixed)},
                    {'name': 'Air pressure', 
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
        # filtering=True,
    	# sorting=True,
    	sort_action='native',
	# sorting_type="multi",
	sort_mode="multi",
	row_selectable="multi",
	row_deletable=False,
	selected_rows=[],
	# pagination_mode="fe",
	# pagination_settings={
        #     "current_page": 0,
	#	    "page_size": 50}
        )
        ])
    return(x)

def homepageDisplay(latestSensorData):
    df2 = latestSensorData.set_index('sensorID', drop = False)
    j = []
    for sID in range(1,5):
        k = [dbc.Card(body = True, children=[    
                dbc.Row([
                    dbc.Col([
                        html.H4('Sensor {:d}'.format(sID)),
                        html.Div('Latest update'),
                        html.Div(df2.at[sID, 'timestamp'])],
                        width = 2,
                    ),
                    dbc.Col(
                        daq.Thermometer(
                        min=-20,
                        max=50,
                        value = df2.at[sID,'data.bmp180_temperature'],
                        showCurrentValue=True,
                        units="C"),
                        width = "auto",
                    ),
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
                    dbc.Col(
                        daq.Gauge(
                        showCurrentValue=True,
                        units="Hectopascals (hPa)",
                        value=df2.at[sID,'data.bmp180_airpressure'],
                        label='Barometer',
                        max=1100,
                        min=1000,
                        size=200,),
                        width = "auto",
                    ),
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
                ])])]
        j.extend(k)
    l= html.Div(children=[
        dbc.Card(
            dbc.CardBody(
            [
                 html.Div(children = j)]
            )
            )
        ])
    return l
    
# def getSensorInfo():
#     # do the same for the sensors info table
#     sensorInfo = pd.DataFrame(json_normalize(json.loads(infoTable.scan()['Items'])))
#     return(sensorInfo)

app.layout = html.Div(className='container', children=[
    dbc.Card(
        dbc.CardBody(
            [
                html.Div(id='header-div', children=[
                    dbc.Row([
                        dbc.Col(html.H1('SDD Sensor App Dashboard'),width=6, align='center'),
                        dbc.Col(dcc.Loading(id="loading-1", children=[html.Div(id="loading-output-1")], type="circle"), width=5, align='center'),
                        dbc.Col(dbc.Button('Refresh', id='refresh-button', className = 'mr-1', color = "primary"), width=1, align='center'),
                    ])
                ]),
            ])),
    dbc.Tabs(id="htmltabs", children=[
        dbc.Tab(id='Homepage', label='Homepage'),
        dbc.Tab(id = 'time-series-tab', label='Graph View'),
        dbc.Tab(id = 'data-table-tab', label='Data Table View'),
        dbc.Tab(id = 'log-messages-tab', label='Log View'),
        dbc.Tab(id = 'about-tab', label='About', children=aboutApp())
    ])])

@app.callback([Output('Homepage', 'children'),
               Output('time-series-tab', 'children'),
               Output('log-messages-tab', 'children'),
               Output('data-table-tab', 'children'),
               Output('loading-output-1', 'children')],
              [Input('refresh-button', 'n_clicks')])
def updateData(n_clicks):
        sensorData = getSensorData()
        timeLastRefreshed = "Data was last refreshed at {:%H:%M:%S on %d %B, %Y}".format(datetime.now())
        sensorInfo = getSensorInfo()
        # updating last obtained data
        maxTimestamps = sensorData.groupby('sensorID')['timestamp'].max().reset_index() 
        latestSensorData = pd.merge(sensorData, maxTimestamps, how='inner') 
        hp = homepageDisplay(latestSensorData)
        tsg = SensorGraph(sensorData)
        itd = infoTableDisplay(sensorInfo)
        dlt = dataTableDisplay(sensorData)
        return(hp, tsg, itd, dlt, timeLastRefreshed)

if __name__ == '__main__':
    app.run_server(debug=True)



