"""Spectroscopy band selection dashboard."""

from __future__ import annotations
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from . import __name__, decoders, raman_tools as raman

import base64
import io
import numpy as np
import os
import pandas as pd
import plotly.express as px

try:
    import redis
    db = redis.Redis(port=6379, password=os.environ["REDIS_AUTH"])
except ModuleNotFoundError:
    db = None


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
        value=[],
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
    dcc.Dropdown(
        id="spectra-bands",
        options=[],
        value=[],
        persistence=True,
        multi=True),
])


# Dashboard HTML
app.layout = html.Main([
    header,
    nav,
    figure,
    dcc.Store(id="cache", data={}),
    dcc.Store(id="db", data={}),
])


@app.callback(
        Output("files-dropdown", "options"),
        Output("files-dropdown", "value"),
        Output("db", "data"),
        Input("files-upload", "contents"),
        State("files-upload", "filename"),
        State("files-dropdown", "value"),
        State("db", "data"))
def select_spectra(contents, filenames, value, data):
    if db is not None:
        if contents and filenames:
            db.hmset("spectrum", dict(zip(filenames, contents)))
        options = sorted(filename.decode("ascii") for filename in db.hkeys("spectrum"))
    else:
        if contents and filenames:
            for filename, content in zip(filenames, contents):
                data[filename] = content
        options = sorted(data)
    if filenames:
        if value is None:
            value = filenames
        else:
            value.extend(filenames)
    return options, value, data


@app.callback(
        Output("cache", "data"),
        Input("preprocessing-transform", "n_clicks"),
        State("files-dropdown", "value"),
        State("preprocessing-checklist", "value"),
        State("cache", "data"),
        State("db", "data"))
def load_spectra(_, filenames, preprocessing, cache, data):
    if not filenames:
        raise PreventUpdate
    if db is not None:
        data = {filename.decode("ascii"): content
                for filename, content in db.hgetall("spectrum")}
    else:
        data = {filename: content.encode("ascii")
                for filename, content in data.items()}
    spectra = {}
    for filename, content in data.items():
        payload = base64.b64decode(content.split(b",")[1])
        if not filename in filenames:
            continue
        stream = io.BytesIO(payload)
        try:
            acquisitions = decoders.load(stream, verbose=0)
        except AttributeError as err:
            print(err)
            continue
        else:
            spectra[filename] = acquisitions.mean(axis=0)
    if not spectra:
        raise PreventUpdate
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


# @app.callback(
#         Output("spectra-graph", "figure"),
#         Input("cache", "data"))
# def plot_spectra(cache):
#     df = pd.read_json(cache["spectra"])
#     return plot(df)


@app.callback(
        Output("spectra-bands", "options"),
        Output("spectra-bands", "value"),
        Output("spectra-graph", "figure"),
        Input("cache", "data"),
        Input("spectra-graph", "selectedData"),
        Input("spectra-bands", "options"),
        Input("spectra-bands", "value"))
def select_bands(cache, selectedData, options, value):
    if "spectra" not in cache:
        raise PreventUpdate
    df = pd.read_json(cache["spectra"]).sort_index()
    if selectedData and "range" in selectedData:
        lower, upper = map(int, selectedData["range"]["x"])
        band = df.loc[lower:upper]
        points = band.to_numpy()
        x, y = np.unravel_index(np.argmax(points), points.shape)
        wavelength = band.iloc[x].name
        options = set(options)
        options.add(wavelength)
        value = set(value)
        value.add(wavelength)
        value = list(value)
    return list(options), value, plot(df, vertical=value)


def discretize(df: pd.DataFrame, copy: bool = False) -> pd.DataFrame:
    """Discretize the index of a dataframe to the closest integral value."""
    if copy:
        df = df.copy()
    df.index = np.round(df.index).astype(int)
    df = df.loc[~df.index.duplicated()]
    df = df.reindex(range(df.index.min(), df.index.max() + 1))
    df = df.interpolate(method="linear")
    return df


def plot(df, vertical: list[int] | None = None):
    fig = px.line(df)
    for coord in (vertical or ()):
        fig.add_vline(x=coord, line_dash="dot")
    fig.update_traces(
            hovertemplate=None)
    fig.update_layout(
            dragmode="select",
            showlegend=False,
            hovermode="x unified")
    return fig
