"""Spectroscopy band selection dashboard."""

from __future__ import annotations
from dash import Dash, dcc, html, Input, Output, State

import base64
import io
import numpy as np
import pandas as pd
import plotly.express as px


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


# Dashboard configuration
app = Dash(__name__)


# Title and description of the dashboard
header = html.Header([
    html.H1(__name__),
])


# Fetching user inputs spectroscopy data
nav = html.Section([
    Upload(id="upload-spectra", multiple=True),
    dcc.Dropdown(id="uploaded-files", multi=True),
    dcc.Checklist(
        id="preprocessing",
        options=["Cosmic Ray Removal", "Savgol", "Raman", "SNV"], 
        value=["Raman"]),
    html.Button("Load spectra from selected files", id="load-button"),
])


# Dashboard HTML
app.layout = html.Main([
    header,
    nav,
    dcc.Graph(id="spectra-graph"),
])


@app.callback(
        Output("uploaded-files", "options"),
        Output("uploaded-files", "value"),
        Input("upload-spectra", "filename"),
        State("uploaded-files", "options"),
        State("uploaded-files", "value"))
def select_spectra(filenames, options, value):
    if filenames:
        return sorted(set(options) | set(filenames)), sorted(set(value) | set(filenames))
    return [], []
