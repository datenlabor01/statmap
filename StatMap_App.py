from dash import Dash, html, dcc, Input, Output, dash_table, ctx
import pandas as pd
import dash_bootstrap_components as dbc

#Mapping-Dictionary für deutsche Länderbezeichnung:
keys_country = pd.read_excel("Country Mapping.xlsx")
keys_country = keys_country[["Recipient name (EN)", "Recipient Name deutsch", "Region", "Continent", "DAC_IncomeGroup"]]
keys_reg = dict(zip(keys_country["Recipient Name deutsch"], keys_country["Region"]))
keys_con = dict(zip(keys_country["Recipient Name deutsch"], keys_country["Continent"]))

#Mapping-Dictionary für Förderbereichschlüssel:
keys_fbs = pd.read_excel("Purpose Codes Mapping.xlsx")
dic_fbs = dict(zip(keys_fbs["DAC 5"].astype(str).str[:3], keys_fbs["DESCRIPTION"]))
dic_fbs_long = dict(zip(keys_fbs["CRS"], keys_fbs["DESCRIPTION"]))

#Funktionen:
#Förderbereichschlüssel nach drei, zwei und ein-ziffrig:
def fbs_subcodes(df, column, fbs_als_zeile):
  #Bilden der ersten drei Ziffern aus Spalte Purpose Code und Bilden der Summe: 
  df['DAC Untercode'] = df["Purpose Code"].astype(str).str[:3]
  df_fbs3 = df.groupby(["DAC Untercode", column])[["Value"]].sum()

  #Wenn FBS als Zeile in die Endtabelle sollen zeilenweise Aufsummieren 
  if fbs_als_zeile == "zeile":
    df_fbs3 = df_fbs3.pivot_table(index = "DAC Untercode", columns = column, aggfunc = "sum", values = "Value")
  #Wenn FBS als Spalte in die Endtabelle sollen spaltenweise Aufsummieren:
  else:
    df_fbs3 = df_fbs3.pivot_table(index = column, columns = "DAC Untercode", aggfunc = "sum", values = "Value")
  
  df_fbs3 = df_fbs3.reset_index()

  #Analog ziehen der ersten zwei Ziffern und Bilden der Summe:
  df['DAC Untercode'] = df["Purpose Code"].astype(str).str[:2]
  df_fbs2 = df.groupby(["DAC Untercode", column])[["Value"]].sum()
  df_fbs2 = df_fbs2.reset_index()
  #Hinzufügen des Strings "0" um Darstellung hervorzuheben:
  df_fbs2["DAC Untercode"] = df_fbs2["DAC Untercode"] + "0"
  
  #Analog spalten- oder zeilenweise Aufsummieren:
  if fbs_als_zeile == "zeile":
    df_fbs2 = df_fbs2.pivot_table(index = "DAC Untercode", columns = column, aggfunc = "sum", values = "Value")
  else:
    df_fbs2 = df_fbs2.pivot_table(index = column, columns = "DAC Untercode", aggfunc = "sum", values = "Value")
  df_fbs2 = df_fbs2.reset_index()
  
  #Ziehen der ersten Ziffer, Bilden der Summe und Hinzufügen von "00" für Unterscheidung:
  df['DAC Untercode'] = df["Purpose Code"].astype(str).str[:1]
  df_fbs1 = df.groupby(["DAC Untercode", column])[["Value"]].sum()
  df_fbs1 = df_fbs1.reset_index()
  df_fbs1["DAC Untercode"] = df_fbs1["DAC Untercode"] + "00"
  
  #Analog spalten- oder zeilenweise Aufsummieren:
  if fbs_als_zeile == "zeile":
    df_fbs1 = df_fbs1.pivot_table(index = "DAC Untercode", columns = column, aggfunc = "sum", values = "Value")
  else:
    df_fbs1 = df_fbs1.pivot_table(index = column, columns = "DAC Untercode", aggfunc = "sum", values = "Value")
  df_fbs1 = df_fbs1.reset_index()

  if fbs_als_zeile != "zeile":
    df_fbs1 = df_fbs1.drop(column, axis = 1)

  return(df_fbs1, df_fbs2, df_fbs3)

#Summen nach Region und Kontinent:
def summe_region_continent (df):

  #Anwenden des Mappings für Kontinent und Region:
  df["Region"] = df["Recipient Name"].map(keys_reg)
  df["Continent"] = df["Recipient Name"].map(keys_con)

  #Summieren nach Regionen und Hinzufügen des Strings ", regional" in Empfängername um Mapping-Tabelle zu entsprechen:
  regions = df.groupby(by = "Region").sum()
  regions = regions.reset_index()
  regions.insert(0, "Recipient Name", regions["Region"] + ", regional")
  #Korrektur des Empfängers ohne Region zu "Nicht aufteilbar" um der Mapping-Tabelle zu entsprechen:
  regions.loc[regions["Recipient Name"] =="Nicht aufteilbar, regional",
            ["Recipient Name"]] = "Nicht aufteilbar"
  #Anwenden des Mappings um Kontinente für Regionen zu erhalten und Hinzufügen des Strings ", total"          
  regions["Continent"] = regions["Recipient Name"].map(keys_con)
  regions["Recipient Name"] = regions["Recipient Name"] + " total"

  #Summieren nach Kontinent und Hinzufügen des Strings ", total Kontinent"
  continents = df.groupby(by = "Continent").sum()
  continents = continents.reset_index()
  continents["Recipient Name"] = continents["Continent"] + ", total Kontinent"
  continents["Region"] = continents["Continent"]

  #Bilden einer Tabelle mit Reihenfolge Kontinente, Regionen und Empfänger
  df_reg_con = pd.concat([continents, regions, df], ignore_index = True)

  return(continents, df_reg_con)

#Sortieren nach Reihenfolge Kontinent, Region und Empfänger:
def order_continent_region(df):
  #Bilden einer Sortierreihenfolge für Kontinente nach Alphabet
  df['Continent'] = pd.CategoricalIndex(df['Continent'], ordered=True, categories=df["Continent"].unique())
  #Sortieren (alphabetisch) nach Kontinent , Region pro Kontinent und Empfänger pro Region 
  df_sorted = df.rename_axis('index').sort_values(by = ['Continent', "Region", "index"])
  
  #Anpassen der Tabellenform mit Empfängername als erste Spalte und ohne Spalte für Region und Kontinent
  df_sorted.insert(0, "Recipient Name", df_sorted.pop("Recipient Name"))
  df_sorted = df_sorted.drop(["Continent", "Region"], axis = 1)

  return df_sorted

#Teilsummen nach Meldern bilden:
def tables_agencies(df):
  #Ziehen der Projekte mit Melder BMZ:
  df_bmz = df.loc[df["Donor Agency"] == "Bundesministerium für Wirtschaftliche Zusammenarbeit und Entwicklung"]
  
  #Ziehen der Projekte des Bundes, d.h. Bundesministerien und Beauftragte für Kultur und Medien  
  searchstring = ['Bundesministerium', 'Staatsminister', "Auswärtiges Amt"]
  df_ministries = df[df["Donor Agency"].str.contains('|'.join(searchstring))]

  #Ziehen der Projekte für Bundesländer:
  searchstring = ['Bundesland', "Bundesländer"]
  df_states = df[df["Donor Agency"].str.contains('|'.join(searchstring))]

  #Ziehen der Projekte für KfW und DEG und Aufsummieren:
  df_kfw = df[(df['Donor Agency'] == 'Kreditanstalt für Wiederaufbau')]
  df_kfw = df_kfw.groupby(["Recipient Name"])[["Value"]].sum()
  df_kfw = df_kfw.rename(columns = {"Value": "KfW"})

  df_deg = df[(df['Donor Agency'] == "Deutsche Investitions- und Entwicklungsgesellschaft")] 
  df_deg = df_deg.groupby(["Recipient Name"])[["Value"]].sum()
  df_deg = df_deg.rename(columns = {"Value": "DEG"})
  
  return [df_bmz, df_ministries, df_states, df_kfw, df_deg]

#Ranking nach Ländern und Melder erstellen:
def ranking_lander(df_bmz, df_ministries, df_states, df_kfw, df_deg):
  #Bilden der Summen für BMZ und Ministerien nach Empfänger:
  df_bmz = df_bmz.groupby(["Recipient Name"])[["Value"]].sum()
  df_bund = df_ministries.groupby(["Recipient Name"])[["Value"]].sum()
  df_ministries = df_ministries[df_ministries["Donor Agency"] != 
  "Bundesministerium für Wirtschaftliche Zusammenarbeit und Entwicklung"].groupby(["Recipient Name"])[["Value"]].sum()
  
  #Aufsummieren für KfW und DEG:
  df_markt = df_kfw.add(df_deg, fill_value=0)
  df_markt["Summe Marktmittel"] = df_markt.sum(axis=1)
  df_markt = df_markt.drop(["DEG", "KfW"], axis = 1)
  #Aufsummieren für Bundesländer:
  df_states = df_states.groupby(["Recipient Name"])[["Value"]].sum()

  tab_oda_melder = pd.concat([df_bund, df_bmz, df_ministries, df_states, df_markt], axis = 1)
  tab_oda_melder.columns = ["Bilaterale ODA Bund", "BMZ", "sonstige Ressorts", "HH Bundesländer", "Marktmittel"]
  tab_oda_melder = tab_oda_melder.reset_index()

  #Löschen der Empfänger als Regionen über Muster mit "," und Eintrag "Nicht aufteilbar"
  tab_oda_melder.drop(tab_oda_melder[tab_oda_melder['Recipient Name'].str.contains(",")].index, inplace = True)
  tab_oda_melder.drop(tab_oda_melder[tab_oda_melder['Recipient Name'] == "Nicht aufteilbar"].index, inplace = True)
  dat_sorted = tab_oda_melder.sort_values("Bilaterale ODA Bund", ascending= False)

  return dat_sorted

#Summe nach Melder und Finanzinstrument bilden: 
def table_ressort_instrument(df_bmz, df_ministries, df_states, df_kfw, df_deg):

  df_bmz = df_bmz.groupby(["Recipient Name", "FinanceType Name"])[["Value"]].sum()
  df_bmz = df_bmz.reset_index()
  df_bmz = df_bmz.pivot_table(index = "Recipient Name", columns = "FinanceType Name", aggfunc = "sum", values = "Value")
  df_bmz.columns = "BMZ " + df_bmz.columns

  df_ministries = df_ministries.groupby(["Recipient Name", "FinanceType Name"])[["Value"]].sum()
  df_ministries = df_ministries.reset_index()
  df_ministries = df_ministries.pivot_table(index = "Recipient Name", columns = "FinanceType Name", aggfunc = "sum", values = "Value")
  df_ministries.columns = "Ressorts " + df_ministries.columns

  df_states = df_states.groupby(["Recipient Name", "FinanceType Name"])[["Value"]].sum()
  df_states = df_states.reset_index()
  df_states = df_states.pivot_table(index = "Recipient Name", columns = "FinanceType Name", aggfunc = "sum", values = "Value")
  df_states.columns = ["Bundesländer"]

  df_bund = df_bmz.add(df_ministries, fill_value=0)
  df_bund["ODA Bund"] = df_bund.sum(axis=1)

  df_markt = df_kfw.add(df_deg, fill_value=0)
  df_markt["Summe Marktmittel"] = df_markt.sum(axis=1)

  df_instrument = df_bund.add(df_markt, fill_value=0)
  df_instrument = df_instrument.add(df_states, fill_value=0)
  df_instrument["ODA Insgesamt"] = df_instrument[["ODA Bund", "Summe Marktmittel", "Bundesländer"]].sum(axis=1)
  df_instrument = df_instrument.reset_index()

  return df_instrument

#Auflistung multilaterale ODA:
def multi_ODA(df):
  df = df[df["Bi/Multi"] == "Multilateral"]
  #Definiere Schlüssel für Channel of Delivery Name zu Channel Category Name und Channel Category Name auf sich selbst
  keys_mo_del = df[["Channel of Delivery Name", "Channel Category Name"]]
  keys_mo_del = dict(zip(keys_mo_del["Channel of Delivery Name"], keys_mo_del["Channel Category Name"]))
  keys_mo_cat = dict(zip(df["Channel Category Name"] + ", total", df["Channel Category Name"]))
  keys_mo = dict(keys_mo_del, **keys_mo_cat)

  #Bilde Summen für Organisation nach Name und Kategorie und lösche Duplikate:
  df_1 = pd.pivot_table(df, index = "Channel of Delivery Name", aggfunc = "sum", columns = "YEAR", values = "Value")
  df_1 = df_1.reset_index()

  df_2 = pd.pivot_table(df, index = "Channel Category Name", aggfunc = "sum", columns = "YEAR", values = "Value")
  df_2 = df_2.reset_index()
  df_2["Channel of Delivery Name"] = df_2["Channel Category Name"]
  df_2["Channel of Delivery Name"] = df_2["Channel of Delivery Name"] + ", total"
  df_2 = df_2.drop("Channel Category Name", axis = 1)
  #Füge Summen zusammen mit Muster Kategorie-Summe und Organisation:
  df_multi = pd.concat([df_2, df_1], ignore_index = True)
  df_multi["Channel Category Name"] = df_multi["Channel of Delivery Name"].map(keys_mo)

  #Sortiere Organisationen nach Kategorie und Name:
  df_multi['Channel Category Name'] = pd.CategoricalIndex(df_multi['Channel Category Name'], 
                                                           ordered=True, categories=df_multi["Channel Category Name"].unique())

  df_multi = df_multi.rename_axis('index').sort_values(by = ['Channel Category Name', "index"])
  df_multi = df_multi.drop("Channel Category Name", axis = 1)

  return df_multi

#Einlesen der Gesamtdatei:
df_ges = pd.read_csv("df_ges.csv")
#Einlesen imputed ODA:
df_imputed = pd.read_csv("df_imputed.csv")
df_imputed.loc[len(df_imputed)] = ["LDC-Anteile an Regionen", "2020", 0, "", "LDCs"]

#Layout:
app = Dash(external_stylesheets = [dbc.themes.LUX])

#Dynamische Elemente:
table_selector = dcc.Dropdown(options=["Bil. ODA nach Empfänger und Melder", "Bil. ODA nach Melder und Finanztyp", "ODA an LDCs",
                              "Bil. ODA nach Empfänger und Förderbereich", "Bil. ODA nach Einkommensgruppe", "Multilaterale ODA nach Empfänger",
                              "Bil. ODA nach Förderbereich und Melder", "Bil. ODA Ranking nach Empfängern", "Mittelherkunft bi./multi. ODA"],
                             value="Tabelle auswählen", id = "tab_sec", style={"textAlign": "center"}, clearable=False)

year_selector = dcc.Dropdown(options=df_ges["YEAR"].unique(), id = "year_sec",
                             value="Jahr auswählen", style={"textAlign": "center"}, clearable=False, multi=True)

row_selector = dcc.Dropdown(options=["Förderbereichschlüssel (dreistellig)", "Förderbereichschlüssel", "Empfänger", "Melder", "Bi-/Multilateral"], id = "row_sec",
                             value="Reihe auswählen", style={"textAlign": "center"}, clearable=False)                      

filter_selector_agency = dcc.Dropdown(options=df_ges["Melder"].unique(), id = "fil_sec",
                             value="Melder auswählen", style={"textAlign": "center"}, clearable=True)

filter_selector_country = dcc.Dropdown(options=df_ges["Recipient Name"].unique(), id = "fil_country",
                             value="Empfänger auswählen", style={"textAlign": "center"}, clearable=True, multi = True)

app.layout = dbc.Container([
  dbc.Row([
  html.Div(html.Img(src="logo.png", style={'height':'80%', 'width':'20%'}))], style={'textAlign': 'center'}),
    
    dbc.Row([
      dbc.Col([dbc.Card(dbc.CardBody([
               html.H4("Aggregierte Tabellen:", className="card-title"),
               table_selector, dbc.Badge(id = "text", className="text-wrap"),
             ]),
            ),
            ]),
      dbc.Col([dbc.Card(dbc.CardBody([
               html.H4("Jahr auswählen:", className="card-title"),
               year_selector,
             ]),
            ),
            ]),
      dbc.Col([dbc.Card(dbc.CardBody([
               html.H3("Tabellen nach Jahren:", className="card-title"),
               html.P("Reihe auswählen:"), row_selector, 
               html.P("Filtern nach:"), filter_selector_agency, filter_selector_country
             ]),
            ),
            ]),
    ]),

    dbc.Row([
        dash_table.DataTable(id="my_table",
        filter_action="native", sort_action="native", page_size= 30, style_cell={'textAlign': 'left', "whiteSpace": "normal", "height": "auto"},
         style_header={'backgroundColor': 'rgb(210, 210, 210)', 'color': 'black', 'fontWeight': 'bold'}, 
         export_format= "xlsx"),
         ]),
])

@app.callback(
    [Output("text", "children"), Output("my_table", 'data'), Output("my_table", "columns")],
    [Input(table_selector, 'value'), Input(year_selector, 'value'), Input(row_selector, 'value'), 
    Input(filter_selector_agency, 'value'), Input(filter_selector_country, 'value')]
)

def get_table(table_selector, year_selector, row_selector, filter_selector_agency, filter_selector_country):
  #Initialiere text-output:
  text = ""
  #Bilden der Grunddatei falls nur ein Jahr ausgewählt wurde, ansonsten 2020 als Default nehmen:
  if (year_selector != "Jahr auswählen") & (5 > len(year_selector)):
    dat = df_ges[df_ges["YEAR"].isin(year_selector)]
  else:
    dat = df_ges[df_ges["YEAR"] == 2020]
  
  #Default-Option einstellen wenn keine Tabelle ausgewählt wurde:
  if table_selector == "Tabelle auswählen":
    dat_sorted = dat

  #Für aggregierte Tabellen anzeigen:
  #Nur in Funktionen gehen wenn Jahr-Button oder Tabellen-Button geklickt wurde: 
  if (ctx.triggered_id != "row_sec") | (ctx.triggered_id != "fil_country") | (ctx.triggered_id != "fil_sec"):

    if table_selector == "Bil. ODA nach Empfänger und Förderbereich":
      [df_fbs1, df_fbs2, df_fbs3] = fbs_subcodes(dat[dat["Bi/Multi"] == "Bilateral"], "Recipient Name", "spalte")
      dfnew = pd.concat([df_fbs2, df_fbs1], axis = 1)
      dfnew = dfnew.sort_index(axis=1)
      dfnew.insert(0, "Recipient Name", dfnew.pop("Recipient Name"))
      dfnew = dfnew.loc[:,~dfnew.columns.duplicated()].copy()

      [continents, tab_fbs_emp] = summe_region_continent(dfnew)
      dat_sorted = order_continent_region(tab_fbs_emp) 
  
    if table_selector == "Bil. ODA nach Melder und Finanztyp":
      [df_bmz, df_ministries, df_states, df_kfw, df_deg] = tables_agencies(dat[dat["Bi/Multi"] == "Bilateral"])
      df_instrument = table_ressort_instrument(df_bmz, df_ministries, df_states, df_kfw, df_deg)
      [continents, tab_instrument] = summe_region_continent(df_instrument)
      dat_sorted = order_continent_region(tab_instrument)

    if table_selector == "ODA an LDCs":
      df_ldcs = dat[dat["Income Group"] == "LDCs"]
      #Nur übernehmen der Jahre nach denen gefiltert wurde:
      years = df_ldcs["YEAR"].unique()
      df_ldcs = pd.concat([df_ldcs, df_imputed[(df_imputed["Income Group"] == "LDCs") & (df_imputed["YEAR"].isin(years))]], axis = 0)  
      #Zusammenfassen der Regionalanteile:
      searchstring = [", regional", "Nicht aufteilbar"]
      df_ldcs.loc[df_ldcs["Recipient Name"].str.contains('|'.join(searchstring)) == True, "Recipient Name"] = "LDC-Anteile an Regionen"
      df_ldcs = df_ldcs.pivot_table(index = ["Recipient Name"], columns = ["Income Group", "YEAR"], aggfunc = "sum", values = "Value")
      df_ldcs = df_ldcs.reset_index()
      #Aufbrechen des Multi-Indexes in den Spaltennamen
      df_ldcs.columns = df_ldcs.columns.map(('{0[1]}'.format))
      dat_sorted = df_ldcs.reset_index()
      #Löschen der Index-Spalte:
      dat_sorted = dat_sorted.iloc[: , 1:]
      text = "Enthält Summe aus imputed multilaterale ODA und bilateraler ODA"
   
    if table_selector == "Bil. ODA nach Einkommensgruppe":
      df_einkommen = dat[dat["Bi/Multi"] == "Bilateral"].pivot_table(index = ["Recipient Name", "Region"], columns = "Income Group", aggfunc = "sum", values = "Value")
      df_einkommen = df_einkommen.reset_index()
      [continents, tab_einkommen] = summe_region_continent(df_einkommen)
      dat_sorted = order_continent_region(tab_einkommen)

    if table_selector == "Bil. ODA nach Förderbereich und Melder":
      [df_fbs1, df_fbs2, df_fbs3] = fbs_subcodes(dat[dat["Bi/Multi"] == "Bilateral"], "Donor Agency", "zeile")
      df_fbs = pd.concat([df_fbs3, df_fbs2, df_fbs1], ignore_index = True)
      df_fbs = df_fbs.drop_duplicates(subset = ["DAC Untercode"])
      df_fbs = df_fbs.sort_values("DAC Untercode")

      df_fbs.insert(0, "Description", df_fbs["DAC Untercode"].map(dic_fbs))
      searchstring = ['Bundesministerium', 'Staatsminister', "Bundestag",
                "Auswärtiges Amt", "Description", "DAC Untercode"]
      dat_sorted = df_fbs.loc[:, df_fbs.columns.str.contains('|'.join(searchstring))]  

    if table_selector == "Bil. ODA nach Empfänger und Melder":
      df = dat[dat["Bi/Multi"] == "Bilateral"].pivot_table(index = "Recipient Name", columns = "Donor Agency", aggfunc = "sum", values = "Value")
      df = df.reset_index()

      [continents, tab_res_emp] = summe_region_continent(df)
      tab_res_emp = order_continent_region(tab_res_emp)
      list_ministries = ['Recipient Name', "Bundesministerium", 'Staatsminister', "Auswärtiges Amt"]
      dat_sorted = tab_res_emp.loc[:, tab_res_emp.columns.str.contains('|'.join(list_ministries))]

    if table_selector == "Bil. ODA Ranking nach Empfängern":
      (df_bmz, df_ministries, df_states, df_kfw, df_deg) = tables_agencies(dat[dat["Bi/Multi"] == "Bilateral"])
      dat_sorted = ranking_lander(df_bmz, df_ministries, df_states, df_kfw, df_deg)

    if table_selector == "Multilaterale ODA nach Empfänger":
      dat_sorted = multi_ODA(dat)

    if table_selector ==  "Mittelherkunft bi./multi. ODA":
      #Suchstring für Bundesministerium, Bundesland und Bundestag: 
      searchstring = ["Bundes", "Staatsminister", "Auswärtiges Amt", "Andere"]
      haushalt = dat[dat["Donor Agency"].str.contains('|'.join(searchstring)) == True]
      searchstring = ["Bundesland", "Bundesländer"]
      haushalt.loc[haushalt["Donor Agency"].str.contains('|'.join(searchstring)) == True, ["Donor Agency"]] = "Bundesländer"
      #Suchstring für KfW und DEG:
      searchstring = ["Kreditanstalt", "Deutsche Investitions- und Entwicklungsgesellschaft"]
      markt = dat[dat["Donor Agency"].str.contains('|'.join(searchstring)) == True]

      #Bilden der Summe für Melder der Bundesregierung und KfW/DEG mit Jahr und Bi/Multi als Spalte:
      haushalt = haushalt.pivot_table(index = "Donor Agency", columns = ["YEAR", "Bi/Multi"], values = "Value", aggfunc = "sum")
      haushalt = haushalt.reset_index()
      markt = markt.pivot_table(index = "Donor Agency", columns = ["YEAR", "Bi/Multi"], values = "Value", aggfunc = "sum")
      markt = markt.reset_index()
      df = pd.concat([haushalt, markt])
      #Aufbrechen des Multi-Indexes in den Spaltennamen und Zusammenführen der Bezeichnung mit Leerzeichen: 
      df.columns = df.columns.map(('{0[0]} {0[1]}'.format))
      dat_sorted = df.reset_index()
      #Löschen der Index-Spalte:
      dat_sorted = dat_sorted.iloc[: , 1:]

  #Tabellen per User-Auswahl:
  #Erster Fall multilaterale ODA, da nur Filter nach Melder:
  if (row_selector == "Bi-/Multilateral") & (ctx.triggered_id != "tab_sec"):
    if ctx.triggered_id == "fil_sec":
      dat = dat[dat["Melder"] == filter_selector_agency]
    df = pd.pivot_table(dat, index = "Melder", columns = ["YEAR", "Bi/Multi"], values = "Value", aggfunc = "sum")
    #Aufbrechen des Multi-Indexes in den Spaltennamen und Zusammenführen der Bezeichnung mit Leerzeichen: 
    df.columns = df.columns.map(('{0[0]} {0[1]}'.format))
    dat_sorted = df.reset_index()

  #Nur in Funktion gehen, wenn Button für aggregierte Tabellen nicht geklickt wurde:
  if ctx.triggered_id != "tab_sec":
    #Datei filtern je nach User-Input:
    if (ctx.triggered_id == "fil_sec") | (ctx.triggered_id == "fil_country"):
      if (filter_selector_country == "Empfänger auswählen") | (filter_selector_country == []): 
        dat = dat[dat["Melder"] == filter_selector_agency]
      else:  
        dat = dat[(dat["Melder"] == filter_selector_agency) & (dat["Recipient Name"].isin(filter_selector_country))]
    #Tabelle nach Empfänger:
    if row_selector == "Empfänger":
      df = pd.pivot_table(dat[dat["Bi/Multi"] == "Bilateral"], index = "Recipient Name", columns = "YEAR", values = "Value", aggfunc = "sum")
      df = df.reset_index()    
      [continent, tab_empfanger_jahre] = summe_region_continent(df)
      dat_sorted = order_continent_region(tab_empfanger_jahre)
    #Tabelle nach FBS:
    if (row_selector == "Förderbereichschlüssel") & (ctx.triggered_id != "tab_sec"):
      dat_sorted = pd.pivot_table(dat[dat["Bi/Multi"] == "Bilateral"], index = "Purpose Code", columns = "YEAR", values = "Value", aggfunc = "sum")
      dat_sorted = dat_sorted.reset_index()
      dat_sorted = dat_sorted.sort_values("Purpose Code")
      #Hinzufügen der Beschreibungen für die Förderbereiche:
      dat_sorted.insert(0, "Description", dat_sorted["Purpose Code"].map(dic_fbs_long))
    #Tabelle nach FBS drei-Ziffrig:
    if (row_selector == "Förderbereichschlüssel (dreistellig)") & (ctx.triggered_id != "tab_sec"):
      [df_fbs1, df_fbs2, df_fbs3] = fbs_subcodes(dat[dat["Bi/Multi"] == "Bilateral"], "YEAR", "zeile")
      dat_sorted = pd.concat([df_fbs1, df_fbs2, df_fbs3], axis = 0)
      dat_sorted = dat_sorted.drop_duplicates(subset = ["DAC Untercode"])
      dat_sorted = dat_sorted.sort_values("DAC Untercode")
      #Hinzufügen der Beschreibungen für die Förderbereiche:
      dat_sorted.insert(0, "Description", dat_sorted["DAC Untercode"].map(dic_fbs))
    #Tabelle nach Melder (vereinfacht):
    if (row_selector == "Melder") & (ctx.triggered_id != "tab_sec"):
      df = pd.pivot_table(dat[dat["Bi/Multi"] == "Bilateral"], index = "Donor Agency", columns = "YEAR", values = "Value", aggfunc = "sum")
      dat_sorted = df.reset_index()

  #Tabelle gemäß User-Input ausgeben:
  rows = dat_sorted.to_dict('rows')
  columns =  [{"name": str(i), "id": str(i),} for i in (dat_sorted.columns)]

  return (text, rows, columns)

if __name__ == '__main__':
    app.run_server(debug=True)
