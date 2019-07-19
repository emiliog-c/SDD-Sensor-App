import dash_html_components as html
import dash_bootstrap_components as dbc

def aboutApp():
    a = html.Div(children=
        dbc.Card(body = True, children=[
            html.H4("About this app", className='card-title'),
            html.H6("Written by Emilio Guevarra Churches", className='card-subtitle'),
            html.P(
                "This website shows all the information that is being compiled by multiple Raspberry Pi Sensors in different locations."
                "The Raspberry Pi's are equipped with Honeywell Particle Sensors (http://www.farnell.com/datasheets/2313714.pdf), capable of measuring PM2.5 and PM10 particles."
                "It is also equipped with an Adafruit DHT22 temperature sensor (https://learn.adafruit.com/dht) and a BMP180 air pressure sensor (https://tutorials-raspberrypi.com/raspberry-pi-and-i2c-air-pressure-sensor-bmp180/)."
                "All code regarding the creation of this project is run with Python, and the libraries Dash, plotly, Bootstrap, the sensors respective libraries, Amazon IoT, Pandas Boto3 and DynamoDB.",
                className="card-text"),       
        ])
    )
                    
    return a
        