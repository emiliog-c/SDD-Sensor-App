import dash_html_components as html
import dash_bootstrap_components as dbc

def aboutApp():
    a = html.Div(children=
        dbc.Card(body = True, children=[
            html.H4("About this app", className='card-title'),
            html.H6("Written by Emilio Guevarra Churches", className='card-subtitle'),
            html.P(
                "Placeholder"
                "placeholder"
                "placeholder",
                className="card-text"),
            html.Img(src="/assets/Basic-structure-of-a-pyrimidine-ring.png"),
            html.P(
                "Placeholder"
                "placeholder"
                "placeholder",
                className="card-text",),
        ])
    )
                    
    return a
        