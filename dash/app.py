import os
import requests
import time
import pandas as pd
import config
from flask import request
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State

external_stylesheets = [
    "https://use.fontawesome.com/releases/v5.0.7/css/all.css",
    'https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css',
    'https://fonts.googleapis.com/css?family=Roboto&display=swap'
]

external_scripts = "https://raw.githubusercontent.com/MarwanDebbiche/post-tuto-deployment/master/src/dash/assets/gtag.js"

app = dash.Dash(
    __name__, 
    external_stylesheets=external_stylesheets,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],
    suppress_callback_exceptions=True
)

app.scripts.append_script({
    "external_url": external_scripts
})

app.title = 'Rishav Sentiment Analysis App'

companies = pd.read_csv('./csv/companies_forbes.csv')
random_reviews = pd.read_csv('./csv/random_reviews.csv')

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

home_layout = html.Div(
    [

        html.Div(
            [
                dcc.Textarea(
                    className="form-control z-depth-1",
                    id="review",
                    rows="8",
                    placeholder="Write something here..."
                )
            ],
            className="form-group shadow-textarea"
        ),

        html.H5(
            'Sentiment analysis 🤖'
        ),

        dbc.Progress(
            children=html.Span(
                id='proba',
                style={
                    'color': 'black',
                    'fontWeight': 'bold'
                }
            ),
            id="progress",
            striped=False,
            animated=True,
            style={
                'marginBottom': '10px'
            }
        ),

        html.H5(
            'Propose a rating 😁📢'
        ),

        html.Div(
            [
                dcc.Slider(
                    id='rating',
                    max=5,
                    min=1,
                    step=1,
                    marks={i: f'{i}' for i in range(1, 6)}
                ),
            ],
            style={'marginBottom': '30px'}
        ),

        html.Button(
            [
                html.Span(
                    "Submit",
                    style={
                        "marginRight": "10px"
                    }
                ),
                html.I(
                    className="fa fa-paper-plane m-l-7"
                )
            ],
            className="btn btn-lg btn-primary btn-block",
            role="submit",
            id="submit_button",
            n_clicks_timestamp=0
        ),

    ],
    className="form-review",
)

admin_layout = html.Div(
    [
        html.H1("Admin Page 🔑"),
        html.Div(id="admin-page-content"),
        html.P(
            dcc.Link("Go to Home 🏡", href="/"),
            style={"marginTop": "20px"}
        )
    ]
)


@app.callback(
    [
        Output('review', 'value'),
        Output('company_link', 'href')
    ],
    [
        Input('submit_button', 'n_clicks_timestamp'),
        Input('switch_button', 'n_clicks_timestamp')
    ],
    [
        State('review', 'value'),
        State('progress', 'value'),
        State('rating', 'value')
    ]
)

@app.callback(
    [
        Output('proba', 'children'),
        Output('progress', 'value'),
        Output('progress', 'color'),
        Output('rating', 'value'),
        Output('submit_button', 'enable')
    ],
    [Input('review', 'value')]
)
def update_proba(review):
    if review is not None and review.strip() != '':
        response = requests.post(
            f"{config.API_URL}/predict", data={'review': review})
        proba = response.json()
        proba = round(proba * 100, 2)
        suggested_rating = min(int((proba / 100) * 5 + 1), 5)
        text_proba = f"{proba}%"

        if proba >= 67:
            return text_proba, proba, 'success', suggested_rating, False
        elif 33 < proba < 67:
            return text_proba, proba, 'warning', suggested_rating, False
        elif proba <= 33:
            return text_proba, proba, 'danger', suggested_rating, False
    else:
        return None, 0, None, 0, True


# Load review table
@app.callback(
    Output('admin-page-content', 'children'),
    [Input('url', 'pathname')]
)
def load_review_table(pathname):
    if pathname != "/admin":
        return None

    response = requests.get(f"{config.API_URL}/reviews")

    reviews = pd.DataFrame(response.json())

    table = dbc.Table.from_dataframe(reviews,
                                     striped=True,
                                     bordered=True,
                                     hover=True,
                                     responsive=True,
                                     header=["id", "brand", "created_date", "review",
                                             "rating", "suggested_rating", "sentiment_score"],
                                     columns=["id", "brand", "created_date", "review",
                                              "rating", "suggested_rating", "sentiment_score"]
                                     )

    return table

# Update page layout


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/':
        return home_layout
    if pathname == "/admin":
        return admin_layout
    else:
        return [
            html.Div(
                [
                    html.Img(
                        src="./assets/404.png",
                        style={
                            "width": "50%"
                        }
                    ),
                ],
                className="form-review"
            ),
            dcc.Link("Go to Home", href="/"),
        ]


if __name__ == '__main__':
    app.run_server(debug=config.DEBUG, host=config.HOST)
