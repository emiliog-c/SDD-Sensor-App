
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
import dash_table
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.plotly as py
import plotly.graph_objs as go
import sys

# create an AWS session, references the .aws/credentials file in home directory
# the credentials file has a section called SDD-Sensors containing the AWS account 
# identifier and secrete key (passowrd) for it to access the DynamoDB database
session = boto3.Session(profile_name='SDD-Sensors')

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
    fe = Key('timestamp').gte('2019-07-03')    
    response = dataTable.scan(FilterExpression=fe)
    data = response['Items']
    while response.get('LastEvaluatedKey'):
        response = dataTable.scan(FilterExpression=fe,
                                    ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
	

# filter records to 1 july 2019 onwards
response = dataTable.scan(FilterExpression=fe)
data = response['Items']
while response.get('LastEvaluatedKey'):
                              ExclusiveStartKey=response['LastEvaluatedKey'])
    data.extend(response['Items'])

    
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
    return sensorData

sensorData = getSensorData()


# print out the dataframe
# print(sensorData)
# show info about the dataframe
print(sensorData.info())

# do the same for the sensors info table
def getSensorInfo():
    fe = Key('timestamp').gte('2019-07-03')    
    response = infoTable.scan(FilterExpression=fe)
    data = response['Items']
    while response.get('LastEvaluatedKey'):
        response = infoTable.scan(FilterExpression=fe,
                                                ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
    sensorInfo = pd.DataFrame(json_normalize(json.loads(data['Items'])))
    return(sensorInfo)

# print out the dataframe
# print(sensorInfo)
# show info about the dataframe
# print(sensorInfo.info())

print(sensorData.groupby('sensorID').count())

# sys.exit()

app = dash.Dash(__name__)

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
    graphdiv = html.Div(children=[
            dcc.Graph(id='temp-graph',figure=make_graph(sensorData, 'data.temperature', 'Temperature', 'degrees Celcius')),
            dcc.Graph(id='humidity-graph', figure=make_graph(sensorData, 'data.humidity', 'Humidity', '% relative humidity')),
            dcc.Graph(id='pm25-graph', figure=make_graph(sensorData, 'data.pm25', 'PM 2.5', 'micrograms per cubic metre')),
            dcc.Graph(id='pm10-graph', figure=make_graph(sensorData, 'data.pm10', 'PM 10', 'micrograms per cubic metre')),
            dcc.Graph(id='bmp180-temp-graph', figure=make_graph(sensorData, 'data.bmp180_temperature', 'Temperature (BMP180 sensor)', 'degrees Celcius')),
            dcc.Graph(id='bmp180-airpress-graph', figure=make_graph(sensorData, 'data.bmp180_airpressure', 'Air pressure', 'Pascals')),
            ])
    return graphdiv

def infoTableDisplay(sensorInfo):
    x = html.Div(children=[	
        dash_table.DataTable(id='info-table', columns=[{"name": i, "id": i} for i in sensorInfo.columns],
            data=sensorInfo.to_dict('records'),
	    editable=False,
            filtering=True,
    	    sorting=True,
	    sorting_type="multi",
	    row_selectable="multi",
	    row_deletable=False,
	    selected_rows=[],
	    pagination_mode="fe",
	    pagination_settings={
                "current_page": 0,
			    "page_size": 50}
                         )
            ])
    return(x)

def getSensorInfo():
    # do the same for the sensors info table
    sensorInfo = pd.DataFrame(json_normalize(json.loads(infoTable.scan()['Items'])))
    return(sensorInfo)



app.layout = html.Div([
    html.Div(id='container-button-basic', children=[
        html.Button('Refresh', id='refresh-button')]),
    dcc.Tabs(id="htmltabs", children=[
        dcc.Tab(label='Homepage', children = [
            html.Div(
                html.H3('Homepage')
            )]),
        dcc.Tab(id = 'time-series-tab', label='Graph View'),
        dcc.Tab(id = 'log-messages-tab', label='List View'),
        dcc.Tab(id = 'data-log-tab', label='Data Log View')
    ])
])

@app.callback([Output('time-series-tab', 'children'), Output('log-messages-tab', 'children'), Output('data-log-tab', 'children')],
              [Input('refresh-button', 'n_clicks')])
def updateData(n_clicks):
        sensorData = getSensorData()
        sensorInfo = getSensorInfo()
        tsg = SensorGraph(sensorData)
        itd = infoTableDisplay(sensorInfo)
        dlt = infoTableDisplay(sensorData)
        return(tsg, itd, dlt)





#@app.callback(Output('htmltabs_stuff', 'children'),
 #             [Input('htmltabs', 'value')])
#def render_content(tab):
#    if tab == 'homepage':
#        html.Div([
 #           html.H3('homepage content'),
  #          
   #     ])
    #elif tab == 'graphview':
     #   return html.Div([
      #      html.H3('graphview content')
       # ])
    #elif tab == 'listview':
    #    return html.Div([
    #        html.H3('listview content')
    #    ])






#app.layout = dash_table.DataTable(
#    id='table',
#    columns=[{"name": i, "id": i} for i in sensorData.columns],
#    data=sensorData.to_dict('records'),#
#	editable=False,
#    filtering=True,
#    sorting=True,
#    sorting_type="multi",
#    row_selectable="multi",
#    row_deletable=False,
#    selected_rows=[],
#    pagination_mode="fe",
#    pagination_settings={
#            "current_page": 0,
#            "page_size": 10,
#    },    
#)

if __name__ == '__main__':
    app.run_server(debug=True)

