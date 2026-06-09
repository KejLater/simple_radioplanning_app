import requests
import numpy as np

from geopy.distance import geodesic

from dash import Dash, html, dcc
from dash.dependencies import Input, Output, State

import dash_leaflet as dl
import plotly.graph_objects as go


N_POINTS = 100
DATASET = "mapzen"


def get_profile(lat1, lon1, lat2, lon2, n=N_POINTS):
    """
    Функция для получения высот между двумя 
    точками без учета кривизны спины слонов,
    которые стоят на краях панциря черепахи.
    """

    lats = np.linspace(lat1, lat2, n)
    lons = np.linspace(lon1, lon2, n)

    locations = "|".join(
        f"{lat},{lon}"
        for lat, lon in zip(lats, lons)
    )

    url = (
        f"https://api.opentopodata.org/v1/"
        f"{DATASET}"
        f"?locations={locations}"
    )

    r = requests.get(url, timeout=30)
    r.raise_for_status()

    data = r.json()

    elevations = [
        x["elevation"]
        for x in data["results"]
    ]

    return np.array(elevations)



def fresnel_radius(f_GHz, d1_km, d2_km):
    """
    Функция для вычисления 
    радиуса первой зоны Френеля.
    """
    if d1_km <= 0 or d2_km <= 0:
        return 0

    return (
        17.32
        * np.sqrt(
            d1_km * d2_km
            / (f_GHz * (d1_km + d2_km))
        )
    )


# =====================================
# Построение профиля
# =====================================

def build_path_profile(
    first_pillar_cors,
    second_pillar_height_m,
    mast1,
    mast2,
    f_GHz
):

    elev = get_profile(
        first_pillar_cors[0],
        first_pillar_cors[1],
        second_pillar_height_m[0],
        second_pillar_height_m[1]
    )

    distance_m = geodesic(
        first_pillar_cors,
        second_pillar_height_m
    ).meters

    x = np.linspace(
        0,
        distance_m,
        len(elev)
    )

    tx = elev[0] + mast1
    rx = elev[-1] + mast2

    los = np.linspace(
        tx,
        rx,
        len(elev)
    )

    d_total_km = distance_m / 1000

    upper = []
    lower = []

    for xi, yi in zip(x, los):

        d1 = xi / 1000
        d2 = d_total_km - d1

        r = fresnel_radius(
            f_GHz,
            d1,
            d2
        )

        upper.append(yi + r)
        lower.append(yi - r)

    return (
        x,
        elev,
        los,
        np.array(upper),
        np.array(lower)
    )



app = Dash(__name__)

app.layout = html.Div(

    [

        html.H2("Радиорелейная линия"),

        html.Div(

            [

                html.Label("Частота (ГГц)"),
                dcc.Input(
                    id="f_GHz",
                    type="number",
                    value=10
                ),

                html.Br(),
                html.Br(),

                html.Label("Высота мачты 1 (м)"),
                dcc.Input(
                    id="mast1",
                    type="number",
                    value=30
                ),

                html.Br(),
                html.Br(),

                html.Label("Высота мачты 2 (м)"),
                dcc.Input(
                    id="mast2",
                    type="number",
                    value=30
                ),

                html.Br(),
                html.Br(),

                html.Button(
                    "Сбросить точки",
                    id="reset",
                    n_clicks=0
                )

            ],

            style={
                "padding": "10px"
            }

        ),

        dcc.Store(
            id="points-store",
            data=[]
        ),

        dl.Map(

            [

                dl.TileLayer(),

                dl.LayerGroup(
                    id="markers-layer"
                )

            ],

            id="map",

            center=[55, 37],

            zoom=4,

            style={
                "height": "500px",
                "width": "100%"
            }

        ),

        html.Br(),

        dcc.Graph(
            id="profile"
        )

    ]

)



@app.callback(
    Output("points-store", "data"),
    Input("map", "clickData"),
    Input("reset", "n_clicks"),
    State("points-store", "data"),
    prevent_initial_call=True
)
def update_points(
    click,
    reset_clicks,
    points
):

    from dash import ctx

    trigger = ctx.triggered_id

    if trigger == "reset":
        return []

    if click is None:
        return points

    lat = click["latlng"]["lat"]
    lon = click["latlng"]["lng"]

    if len(points) >= 2:
        points = []

    points.append([lat, lon])

    return points



@app.callback(
    Output("markers-layer", "children"),
    Input("points-store", "data")
)
def update_markers(points):

    markers = []

    for i, point in enumerate(points):

        markers.append(

            dl.Marker(

                position=point,

                children=[
                    dl.Tooltip(
                        f"P{i+1}"
                    )
                ]

            )

        )

    if len(points) == 2:

        markers.append(

            dl.Polyline(
                positions=points,
                color="red"
            )

        )

    return markers



@app.callback(
    Output("profile", "figure"),
    Input("points-store", "data"),
    Input("f_GHz", "value"),
    Input("mast1", "value"),
    Input("mast2", "value")
)
def update_profile(
    points,
    f_GHz,
    mast1,
    mast2
):

    fig = go.Figure()

    if len(points) != 2:
        fig.update_layout(
            title="Выберите две точки"
        )
        return fig

    try:

        x, elev, los, upper, lower = build_path_profile(
            points[0],
            points[1],
            mast1,
            mast2,
            f_GHz
        )

        
        base = elev.min() - 5

        # Рельеф
        fig.add_trace(
            go.Scatter(
                x=np.concatenate([x, x[::-1]]),
                y=np.concatenate([
                    elev,
                    np.full_like(elev, base)[::-1]
                ]),
                fill="toself",
                mode="lines",
                name="Рельеф"
            )
        )

        
        fig.add_trace(
            go.Scatter(
                x=np.concatenate([x, x[::-1]]),
                y=np.concatenate([
                    upper,
                    lower[::-1]
                ]),
                fill="toself",
                mode="lines",
                opacity=0.25,
                name="1-я зона Френеля"
            )
        )

      
        fig.add_trace(
            go.Scatter(
                x=x,
                y=los,
                mode="lines",
                name="LOS"
            )
        )

       
        fig.add_trace(
            go.Scatter(
                x=[0, 0],
                y=[
                    elev[0],
                    elev[0] + mast1
                ],
                mode="lines",
                name="Мачта 1"
            )
        )

       
        fig.add_trace(
            go.Scatter(
                x=[x[-1], x[-1]],
                y=[
                    elev[-1],
                    elev[-1] + mast2
                ],
                mode="lines",
                name="Мачта 2"
            )
        )

        ymin = min(
            base,
            lower.min()
        )

        ymax = max(
            upper.max(),
            elev.max()
        )

        fig.update_layout(
            title="Профиль трассы",
            template="plotly_white",
            xaxis_title="Расстояние (м)",
            yaxis_title="Высота (м)",
            showlegend=True
        )

        fig.update_yaxes(
            range=[
                ymin,
                ymax + 10
            ]
        )

    except Exception as e:

        fig.update_layout(
            title=str(e)
        )

    return fig


if __name__ == "__main__":
    app.run(debug=False, port=5000)