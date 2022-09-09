"""Spectroscopy band selection dashboard."""

from __future__ import annotations
from dash import Dash, dcc, html, Input, Output, State

import base64
import io
import numpy as np
import os
import pandas as pd
import plotly.express as px
import redis


def Upload(id, multiple: bool = False):
    text = html.Div([
        "Drag and Drop or ",
        html.A(html.B("Select Files"))])
    style = {
        'width': '100%',
        'height': '60px',
        'lineHeight': '60px',
        'borderWidth': '1px',
        'borderStyle': 'dashed',
        'borderRadius': '5px',
        'textAlign': 'center',
        'margin': '10px'}
    return dcc.Upload(id=id, children=text, style=style, multiple=multiple)


# Database configuration
db = redis.Redis(port=6379, password=os.environ["REDIS_AUTH"])


# Dashboard configuration
app = Dash(
        __name__,
        external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])



# Title and description of the dashboard
header = html.Header([
    html.H1(__name__),
])


# Fetching user inputs spectroscopy data
nav = html.Section([
    Upload(id="files-upload", multiple=True),
    dcc.Dropdown(
        id="files-dropdown",
        persistence=True,
        multi=True),
    dcc.Checklist(
        id="preprocessing-checklist",
        options=["Cosmic Ray Removal", "Savgol", "Raman", "SNV"], 
        persistence=True,
        value=["Raman"]),
    html.Button(
        "Load spectra from selected files",
        id="preprocessing-transform")])


# Dashboard HTML
app.layout = html.Main([
    header,
    nav,
    dcc.Graph(id="spectra-graph"),
])


@app.callback(
        Output("files-dropdown", "options"),
        Input("files-upload", "contents"),
        State("files-upload", "filename"))
def select_spectra(contents, filenames):
    if contents and filename:
        db.hmset("spectrum", dict(zip(filenames, contents)))
    options = sorted(filename.decode("ascii") for filename in db.hkeys("spectrum"))
    return options
