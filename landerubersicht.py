import plotly.express as px
import pandas as pd
pd.options.mode.chained_assignment = None
from dash import Dash, html, dcc, Input, Output, dash_table, State
import dash_bootstrap_components as dbc

df_data = pd.read_csv("https://raw.githubusercontent.com/datenlabor01/LS/main/landubersicht_data.csv")
df_data["Value"] = round(df_data["Value"], 2)
app = Dash(external_stylesheets = [dbc.themes.LUX])

#Dropdown for indicator: 
indicator_dropdown = dcc.Dropdown(options=sorted(df_data["Series"].unique()),
                             value='All', style={"textAlign": "center"}, clearable=False, multi=False, placeholder='Indikatoren auswählen (Default: DEU ODA)')

#Dropdown for country:
country_dropdown = dcc.Dropdown(options=sorted(df_data["Country"].unique()),
                             value='All', style={"textAlign": "center"}, clearable=False, multi=False, placeholder='Land auswählen (Default: Iran)')

#Slider for year:
year_slider = dcc.Slider(df_data.Year.min(), df_data.Year.max(), step = 1,
                          value = df_data.Year.min(), included=False)

text2 = "Diese Anwendung wird als Prototyp vom BMZ Datenlabor angeboten. Sie kann Fehler enthalten und ist als alleinige Entscheidungsgrundlage nicht geeignet. Außerdem können Prototypen ausfallen oder kurzfristig von uns verändert werden. Sichern Sie daher wichtige Ergebnisse per Screenshot oder Export. Die Anwendung ist vorerst intern und sollte daher nicht ohne Freigabe geteilt werden. Wenden Sie sich bei Fragen gerne an datenlabor@bmz.bund.de"

app.layout = dbc.Container([
      dbc.Row([
         html.Div(html.Img(src="https://github.com/datenlabor01/LS/raw/main/logo.png", style={'height':'80%', 'width':'20%'})),
         html.H1(children='Prototyp Länderüberblick'),
         html.P(children = "Das ist ein Prototyp, der Fehler enthalten kann. Skript, Datenquellen und Erklärungen sind aufrufbar unter https://github.com/datenlabor01/LS.")],
         style={'textAlign': 'center'}),

      dbc.Row([
         dbc.Button(children = "Über diese App", id = "textbutton", color = "light", className = "me-1",
                    n_clicks=0, style={'textAlign': 'center', "width": "30rem"})
      ], justify = "center"),
      dbc.Row([
            dbc.Collapse(dbc.Card(dbc.CardBody([
               dbc.Badge(text2, className="text-wrap"),
               ])), id="collapse", style={'textAlign': 'center', "width": "60rem"}, is_open=False),
      ], justify = "center"),

      dbc.Row([
        dbc.Col([indicator_dropdown, html.Br(), year_slider], width = 8),
      ], justify = "center"),

      dbc.Row([
         dcc.Graph(id='map', style={'textAlign': 'center'}),
      ]),

      dbc.Row([dbc.Col([
         dcc.Graph(id='buble_chart')],width = 10),
      ],justify = "center"),
      
      dbc.Row([
        dbc.Col([country_dropdown, html.Br()], width = 8),
      ],justify = "center"),

      dbc.Row([
         dbc.Col([dcc.Graph(id='line_chart', style={'textAlign': 'center'})]),
         dbc.Col([dcc.Graph(id='per_chart', style={'textAlign': 'center'})]),
         dbc.Col([dcc.Graph(id='score_chart', style={'textAlign': 'center'})]),
      ]),

      #Data Table:
      dbc.Row([
         my_table := dash_table.DataTable(
         df_data.to_dict('records'), [{"name": i, "id": i} for i in df_data.columns],
         filter_action="native", sort_action="native", page_size= 25,
         style_cell={'textAlign': 'left', "whiteSpace": "normal", "height": "auto"},
         style_header={'backgroundColor': 'rgb(11, 148, 153)', 'color': 'black', 'fontWeight': 'bold'},
             style_data_conditional=[{
            'if': {'row_index': 'odd'},
            'backgroundColor': 'rgb(235, 240, 240)',
        }], export_format= "xlsx"),
         ]),
])

#Button to display text:
@app.callback(
    Output("collapse", "is_open"),
    [Input("textbutton", "n_clicks")],
    [State("collapse", "is_open")],
)

def collapse(n, is_open):
   if n:
      return not is_open
   return is_open

#Show only available years in slider:
@app.callback(
    [Output(year_slider, "marks"), Output(year_slider, "max"), 
     Output(year_slider, "min"), Output(year_slider, 'value')],
    Input(indicator_dropdown, 'value'))

def year_options(selected_indicator):
   if (selected_indicator == "All") | (selected_indicator == []):
      dat_temp = df_data[df_data["Series"] == "Gross_ODA_Germany (in US$)"]
   else:
      dat_temp = df_data[df_data["Series"] == selected_indicator]
   #Get available years in filtered dataframe:
   slider_txt = dat_temp["Year"].unique()
   slider_txt = slider_txt.tolist()
   min_slider = 0
   max_slider = len(slider_txt)-1
   marks_slider ={i: '{}'.format(slider_txt[i]) for i in range(0, len(slider_txt))}
   slider_value = min_slider
   return marks_slider, max_slider, min_slider, slider_value

@app.callback(
    [Output('map', 'figure'), Output('buble_chart', 'figure')],
    [Input(indicator_dropdown, 'value'), Input(year_slider, 'value')]
)

def update_map(selected_indicator, year_slider):

   if (selected_indicator == "All") | (selected_indicator == None):
      dat_map = df_data[df_data["Series"] == "Gross_ODA_Germany (in US$)"]
      selected_indicator = "Gross_ODA_Germany (in US$)"
   else:
      dat_map = df_data[df_data["Series"] == selected_indicator]

   slider_txt = dat_map["Year"].unique()
   dat_map = dat_map[dat_map["Year"] == slider_txt[year_slider]]
   dat_table_full = df_data.pivot_table(index=['Country', "Year"], columns='Series', values='Value').reset_index()

   figMap = px.choropleth(dat_map, locations = "index", locationmode="ISO-3", hover_data= ["Country", "Series"],
                        color_continuous_scale="Fall", color="Value", range_color=(min(dat_map["Value"]), max(dat_map["Value"])))
   if slider_txt[year_slider] in df_data[df_data["Series"] == "Gross_ODA_Germany (in US$)"]["Year"].unique():
      figBubble = px.scatter(dat_table_full[dat_table_full.Year == slider_txt[year_slider]], 
                             x='GDP current prices (in US$)', y= selected_indicator, color = "Country",
	         size="Gross_ODA_Germany (in US$)", log_x=True, size_max=80)
      title_txt ="Gewählter Indikator wird zur y-Achse. x-Achse ist GDP, Blasengröße BMZs Brutto ODA"
   else:
      figBubble = px.scatter()
      title_txt = "Für gewähltes Jahr fehlen Daten"
   
   figBubble.update_layout(showlegend=False, title = title_txt, title_x=0.5)

   return figMap, figBubble

@app.callback(
    [Output('line_chart', 'figure'),
     Output('per_chart', 'figure'), Output('score_chart', "figure"),
     Output(my_table, "data"), Output(my_table, "columns")],
    Input(country_dropdown, 'value')
)

def update_figures(selected_country):

   dat_table_full = df_data.pivot_table(index=['Country', "Year"], columns='Series', values='Value').reset_index()

   if ("All" == selected_country) | (selected_country == None):
      dat_fil = df_data[df_data["Country"] == "Iran"]
      dat_table = dat_table_full
   else:
      dat_fil = df_data[df_data["Country"] == selected_country]
      dat_table = dat_table_full[dat_table_full["Country"] == selected_country]

   dat_fil['Year'] = dat_fil['Year'].astype(str)
   df1 = dat_fil[(dat_fil['Series'].str.contains("US"))&(dat_fil['Series'] != 'GDP current prices (in US$)')]

   figLine = px.line(df1, x='Year', y='Value', color ="Series", log_y=True)
   figLine.add_traces(px.line(dat_fil[dat_fil['Series'] == 'GDP current prices (in US$)'], 
                                 x='Year', y='Value', color ="Series", symbol="Series").update_traces(yaxis='y2').data)
   figLine.update_layout(showlegend=False, yaxis=dict(title='in USD'), 
                  yaxis2=dict(title='GDP in USD (blue dotted line)', overlaying='y', side='right'))
   
   searchstring = ["Corruption_Perception_Index", "Gini index", 
                   "Governance_Index", "HDI-Score", "Environment_Policy_Index"]
   figScore = px.line(dat_fil[dat_fil.Series.str.contains('|'.join(searchstring))], x="Year", y="Value", color='Series', symbol="Series")
   figScore.update_layout(showlegend=False, yaxis=dict(title='Scales from 0-100'))

   figPercent = px.line(dat_fil[dat_fil.Series.str.contains("%")], x="Year", y="Value", color='Series', symbol="Series")
   figPercent.update_layout(showlegend=False, yaxis=dict(title='in %'))

   return figLine, figPercent, figScore, dat_table.to_dict("records"), [{"name": i, "id": i} for i in dat_table.columns]

if __name__ == '__main__':
    app.run_server(debug=True)