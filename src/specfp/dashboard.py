"""Spectroscopy band selection dashboard."""

from __future__ import annotations
from dash import Dash, dcc, html, Input, Output, State
from . import __name__, decoders, raman_tools as raman

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

figure = html.Div(id="spectra", children=[
    dcc.Graph(id="spectra-graph"),
    dcc.Dropdown(id="spectra-bands", value=[], persistence=True, multi=True),
])


# Dashboard HTML
app.layout = html.Main([
    header,
    nav,
    figure,
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


@app.callback(
        Output("cache", "data"),
        Input("preprocessing-transform", "n_clicks"),
        State("files-dropdown", "value"),
        State("preprocessing-checklist", "value"),
        State("cache", "data"))
def load_spectra(_, filenames, preprocessing, cache):
    if not filenames:
        return {}
    data = db.hgetall("spectrum")
    spectra = {}
    for filename, content in data.items():
        filename = filename.decode("ascii")
        if not filename in filenames:
            continue
        _, content = content.split(b",")
        stream = io.BytesIO(base64.b64decode(content))
        try:
            acquisitions = decoders.load(stream, verbose=0)
        except AttributeError:
            continue
        else:
            spectra[filename] = acquisitions.mean(axis=0)
    df = discretize(pd.DataFrame(spectra).sort_index())
    df.index.name = "wavelength"
    if "Cosmic Ray Removal" in preprocessing:
        df = df.apply(raman.cosmic_rays_removal, raw=True)
    if "Savgol" in preprocessing:
        df = df.apply(
                raman.savgol_filter,
                raw=True,
                window_length=11,
                polyorder=3)
    if "Raman" in preprocessing:
        df = df.apply(raman.bubblefill, raw=True)
    if "SNV" in preprocessing:
        df = df.apply(raman.SNV, raw=True)
    cache["spectra"] = str(df.to_json())
    return cache


@app.callback(
        Output("spectra-graph", "figure"),
        Input("cache", "data"))
def plot_spectra(cache):
    df = pd.read_json(cache["spectra"])
    return plot(df)


def discretize(df: pd.DataFrame, copy: bool = False) -> pd.DataFrame:
    """Discretize the index of a dataframe to the closest integral value."""
    if copy:
        df = df.copy()
    df.index = np.round(df.index).astype(int)
    df = df.loc[~df.index.duplicated()]
    df = df.reindex(range(df.index.min(), df.index.max() + 1))
    df = df.interpolate(method="linear")
    return df


def plot(df):
    labels={'value': 'Absorption',
            'wavelength': 'Wavelength (nm)',
            'variable': 'Acquisition'}
    fig = px.line(df, labels=labels, hover_name="variable")
    fig.update_layout(
            dragmode="select",
            showlegend=False,
            hovermode="x unified")
    return fig
