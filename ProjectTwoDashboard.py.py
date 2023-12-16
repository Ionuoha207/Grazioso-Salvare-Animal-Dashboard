# Setup the Jupyter version of Dash
from jupyter_dash import JupyterDash

# Configure the necessary Python module imports for dashboard components
import dash_leaflet as dl
from dash import dcc
from dash import html
import plotly.express as px
from dash import dash_table
from dash.dependencies import Input, Output, State
import base64

# Configure OS routines
import os

# Configure the plotting routines
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from animals_shelter import AnimalShelter

###########################
# Data Manipulation / Model
###########################
# Connect to the database
db_name = 'AAC'
collection_name = 'animals'
username = 'aacuser'
password = '1234'
host = 'nv-desktop-services.apporto.com'
port = 31150

db = AnimalShelter(db_name, collection_name, host, port, username, password)
df = pd.DataFrame.from_records(db.read({}))
df.drop(columns=['_id'], inplace=True)


#########################
# Dashboard Layout / View
#########################
app = JupyterDash(__name__)

# Incorporate Grazioso Salvare’s logo
image_filename = 'Grazioso Salvare Logo.png'
encoded_image = base64.b64encode(open(image_filename, 'rb').read()).decode()

app.layout = html.Div([
    html.Center(html.B(html.H1('CS-340 Dashboard'))),
    html.Hr(),
    html.Div([
        html.A(html.Img(src=f'data:image/png;base64,{encoded_image}',
                        alt='Grazioso Salvare Logo',
                        style={'height': '50px'}),
               href='https://www.snhu.edu', target='_blank'),
        html.P('Created by: Ikechukwu Ionuaho')
    ]),
    html.Hr(),
    html.Div([
        dcc.RadioItems(
            id='filter-type',
            options=[
                {'label': 'Water Rescue', 'value': 'water'},
                {'label': 'Mountain or Wilderness Rescue', 'value': 'mountain'},
                {'label': 'Disaster Rescue or Individual Tracking', 'value': 'disaster'},
                {'label': 'Reset', 'value': 'reset'}
            ],
            value='reset',
            labelStyle={'display': 'block'}
        )
    ]),
    html.Hr(),
    dash_table.DataTable(
        id='datatable-id',
        columns=[{"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns],
        data=df.to_dict('records'),
        # Set up features to make the data table user-friendly
        filter_action='native',  # Enables filtering
        sort_action='native',    # Enables sorting
        sort_mode='multi',       # Allows multi-column sorting
        column_selectable='single',  # Allows users to select columns
        row_selectable='single',     # Allows users to select rows
        selected_columns=[],     # Used for highlighting columns
        selected_rows=[],        # Used for highlighting rows
        page_action='native',    # Enables pagination
        page_current=0,          # Current page
        page_size=10,            # Number of rows per page
    ),
    html.Br(),
    html.Hr(),
    html.Div(className='row', style={'display': 'flex'}, children=[
        html.Div(id='graph-id', className='col s12 m6'),
        html.Div(id='map-id', className='col s12 m6')
    ])
])

#############################################
# Interaction Between Components / Controller
#############################################

# Callback for updating the data table based on the selected filter type
@app.callback(
    Output('datatable-id', 'data'),
    [Input('filter-type', 'value')])
def update_dashboard(filter_type):
    query = {}
    
    if filter_type == 'water':
        query = {
            'breed': {
                '$in': [
                    'Labrador Retriever Mix', 'Chesapeake Bay Retriever', 'Newfoundland'
                ]
            },
            'sex_upon_outcome': 'Intact Female',
            'age_upon_outcome_in_weeks': {'$gte': 26, '$lte': 156}
        }
    elif filter_type == 'mountain':
        query = {
            'breed': {
                '$in': [
                    'German Shepherd', 'Alaskan Malamute', 'Old English Sheepdog',
                    'Siberian Husky', 'Rottweiler'
                ]
            },
            'sex_upon_outcome': 'Intact Male',
            'age_upon_outcome_in_weeks': {'$gte': 26, '$lte': 156}
        }
    elif filter_type == 'disaster':
        query = {
            'breed': {
                '$in': [
                    'Doberman Pinscher', 'German Shepherd', 'Golden Retriever', 
                    'Bloodhound', 'Rottweiler'
                ]
            },
            'sex_upon_outcome': 'Intact Male',
            'age_upon_outcome_in_weeks': {'$gte': 20, '$lte': 300}
        }
    elif filter_type == 'reset':
        query = {}

    df_filtered = pd.DataFrame.from_records(db.read(query))

    if '_id' in df_filtered.columns:
        df_filtered.drop(columns=['_id'], inplace=True)

    return df_filtered.to_dict('records')


# Callback for updating the chart based on the data table
@app.callback(
    Output('graph-id', "children"),
    [Input('datatable-id', "derived_virtual_data")])
def update_graphs(viewData):
    # Ensure that viewData is not empty
    if viewData is None or not viewData:
        return dcc.Graph()  # Return an empty graph if no data
    else:
        dff = pd.DataFrame.from_dict(viewData)
        # Ensure that 'breed' column exists before plotting
        if 'breed' in dff.columns:
            # Group by breed and count the occurrences
            breed_counts = dff['breed'].value_counts().reset_index()
            breed_counts.columns = ['breed', 'count']
            fig = px.pie(breed_counts, names='breed', values='count', title='Distribution of Breeds')
            return dcc.Graph(figure=fig)
        else:
            return dcc.Graph()  # Return an empty graph if 'breed' column doesn't exist

# Callback for highlighting selected columns in the data table
@app.callback(
    Output('datatable-id', 'style_data_conditional'),
    [Input('datatable-id', 'selected_columns')])
def update_styles(selected_columns):
    return [{
        'if': {'column_id': i},
        'background_color': '#D2F3FF'
    } for i in selected_columns]

# Callback for updating the map based on the selected row in the data table
@app.callback(
    Output('map-id', "children"),
    [Input('datatable-id', "derived_virtual_data"),
     Input('datatable-id', "derived_virtual_selected_rows")])
def update_map(viewData, derived_virtual_selected_rows):
    # Check if viewData and the selected_rows list is not empty
    if viewData is None or derived_virtual_selected_rows is None or not derived_virtual_selected_rows:
        # Return a default map if no data or no row is selected
        return dl.Map(style={'width': '1000px', 'height': '500px'}, center=[30.75, -97.48], zoom=10, children=[dl.TileLayer()])
    else:
        dff = pd.DataFrame.from_dict(viewData)
        row = derived_virtual_selected_rows[0]  # We use the first selected row
        # Check if the DataFrame has enough rows and the required columns before accessing the data
        if not dff.empty and row < len(dff) and 'location_lat' in dff.columns and 'location_long' in dff.columns:
            # Construct the map with the marker set to the selected row's location
            return [
                dl.Map(style={'width': '1000px', 'height': '500px'}, center=[dff.iloc[row]['location_lat'], dff.iloc[row]['location_long']], zoom=10, children=[
                    dl.TileLayer(),
                    dl.Marker(position=[dff.iloc[row]['location_lat'], dff.iloc[row]['location_long']], children=[
                        dl.Tooltip(dff.iloc[row]['animal_type']),
                        dl.Popup([
                            html.H1("Animal Name"),
                            html.P(dff.iloc[row]['name'])
                        ])
                    ])
                ])
            ]
        else:
            # Return a default map if the required columns are not present or the row index is out of bounds
            return dl.Map(style={'width': '1000px', 'height': '500px'}, center=[30.75, -97.48], zoom=10, children=[dl.TileLayer()])

app.run_server(debug=True)
