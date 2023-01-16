import pandas as pd

#Mapping-Dictionary für deutsche Länderbezeichnung:
keys_country = pd.read_excel("Country Mapping.xlsx")
keys_country = keys_country[["Recipient name (EN)", "Recipient Name deutsch", "Region", "Continent", "DAC_IncomeGroup"]]
keys_rec_deutsch = dict(zip(keys_country["Recipient name (EN)"], keys_country["Recipient Name deutsch"]))
keys_reg = dict(zip(keys_country["Recipient Name deutsch"], keys_country["Region"]))
keys_con = dict(zip(keys_country["Recipient Name deutsch"], keys_country["Continent"]))
keys_inc = dict(zip(keys_country["Recipient Name deutsch"], keys_country["DAC_IncomeGroup"]))

#Mapping-Dictionary für Förderbereichschlüssel:
keys_fbs = pd.read_excel("Purpose Codes Mapping.xlsx")
dic_fbs = dict(zip(keys_fbs["DAC 5"].astype(str).str[:3], keys_fbs["DESCRIPTION"]))
dic_fbs_long = dict(zip(keys_fbs["CRS"], keys_fbs["DESCRIPTION"]))

#Mapping-Dictionary für deutsche Bezeichnung für Donor Agencies:  
keys_donoragency = pd.read_excel("Donor Agency Mapping.xlsx")
keys_donoragency_deutsch = dict(zip(keys_donoragency["Donor Agency"], keys_donoragency["Donor Agency Deutsch"]))
keys_donoragency_kurz = dict(zip(keys_donoragency["Donor Agency Deutsch"], keys_donoragency["Abkürzung"]))

#Funktionen:
#Einlesen der bilateralen Dateien und Mapping auf deutsche Bezeichnungen:
def reader(string1, string2, string3):
    
    df1 = pd.read_csv(string1, sep='|', encoding = "ISO 8859-1")
    df2 = pd.read_csv(string2, sep='|', encoding = "ISO 8859-1")
    df3 = pd.read_csv(string3, sep='|', encoding = "ISO 8859-1")
    df_bil = pd.concat([df1, df2, df3])
    df_bil = df_bil.reset_index()

    #Delete non-German projects: 
    df_bil = df_bil.drop(df_bil[df_bil.DonorName != "Germany"].index)
    #Delete non-ODA projects:
    df_bil = df_bil.drop(df_bil[df_bil.FlowName == "Other Official Flows (non Export Credit)"].index)
    df_bil = df_bil.drop(df_bil[df_bil.FlowName == "Private Development Finance"].index)

    #Keep only columns relevant for calculations:
    df_bil = df_bil[["DonorName", "Year", "AgencyName", "ProjectNumber", "RecipientName", "IncomegroupName", "USD_Commitment", "USD_Disbursement",
    "USD_Received", "PurposeCode", "LDCflagName","Bi_Multi", "GrantEquiv", "ProjectTitle", "Finance_t"]]

    #Rename columns for consistency:
    df_bil.rename(columns = {'Bi_Multi':'Bi/Multi', 'PurposeCode': 'Purpose Code', 'ProjectNumber': 'Donor Project ID', "Year": "YEAR",
    'ProjectTitle':'Project title', 'Finance_t':'FinanceType Name'}, inplace = True)
    
    #Rename bilateral and multilateral:
    df_bil.loc[df_bil["Bi/Multi"] != "2.", ["Bi/Multi"]] = "Bilateral"
    df_bil.loc[df_bil["Bi/Multi"].isnull() == True, ["Bi/Multi"]] = "Bilateral"

    #Change terminology of unspecified recipients and replace nans:   
    df_bil.loc[df_bil["RecipientName"].isna() == True, ["RecipientName"]] = "Developing countries, unspecified"
    df_bil.loc[df_bil["RecipientName"] == "Bilateral, unspecified", ["RecipientName"]] = "Developing countries, unspecified"

    #Map German names for recipient, income group, region and continent:
    df_bil["Recipient Name"] = df_bil["RecipientName"].map(keys_rec_deutsch)
    df_bil["Continent"] = df_bil["Recipient Name"].map(keys_con)
    df_bil["Income Group"] = df_bil["Recipient Name"].map(keys_inc)
    df_bil["Region"] = df_bil["Recipient Name"].map(keys_reg)

    #Change income group of regional projects with exact LDC-calculation to LDC:
    df_bil.loc[df_bil["LDCflagName"] == "Exact expenditure", ["Income Group"]] = "LDCs"
  
    #Für Projekte der DEG: Füge unter Spalte Donor Agency Namen zu da leer im Originaldatensatz:
    df_bil.loc[df_bil["AgencyName"].isna() == True, ["AgencyName"]] = "German Investment and Development Company"
    #Mappen der deutschen Bezeichnungen für Donor Agencies:
    df_bil["Donor Agency"] = df_bil["AgencyName"].map(keys_donoragency_deutsch)

    #Get Grant Equivalent:
    df_bil['USD_Disbursement'] = df_bil['USD_Disbursement'].fillna(0)
    df_bil['USD_Received'] = df_bil['USD_Received'].fillna(0)
    df_bil["Value"] = 0
    df_bil.loc[(df_bil["FinanceType Name"] == 110), ["Value"]] = df_bil.USD_Disbursement
    df_bil.loc[(df_bil["FinanceType Name"] == 421) | (df_bil["FinanceType Name"] == 610), ["Value"]] = df_bil.GrantEquiv
    df_bil.loc[(df_bil["FinanceType Name"] == 510) | (df_bil["FinanceType Name"] == 520), ["Value"]] = df_bil.USD_Disbursement - df_bil.USD_Received
    #Exception for 2018 and 2019 for valuation of debt cancellation:
    df_bil.loc[(df_bil["FinanceType Name"] == 611) & (df_bil["YEAR"] == 2018), ["Value"]] = df_bil.USD_Disbursement
    df_bil.loc[(df_bil["FinanceType Name"] == 611) & (df_bil["YEAR"] == 2019), ["Value"]] = df_bil.USD_Disbursement

    #Change Type of Finance to names:
    df_bil.loc[(df_bil["FinanceType Name"] == 110), "FinanceType Name"] = "Zuschuss"
    df_bil.loc[(df_bil["FinanceType Name"] == 421), "FinanceType Name"] = "Darlehen"
    df_bil.loc[(df_bil["FinanceType Name"] == 510), "FinanceType Name"] = "Equity"
    df_bil.loc[(df_bil["FinanceType Name"] == 520), "FinanceType Name"] = "Anteil an Investitionsvehikel"
    df_bil.loc[(df_bil["FinanceType Name"] == 611), "FinanceType Name"] = "Schuldenerlass"
    df_bil.loc[(df_bil["FinanceType Name"] == 610), "FinanceType Name"] = "Schuldenerlass"

    # #Convert to EUR:
    df_bil.loc[df_bil["YEAR"] == 2018, "Value"] = df_bil.Value * 0.8473 
    df_bil.loc[df_bil["YEAR"] == 2019, "Value"] = df_bil.Value * 0.8933
    df_bil.loc[df_bil["YEAR"] == 2020, "Value"] = df_bil.Value * 0.8775

    #Delete projects that have value 0 or are empty:
    df_bil = df_bil.drop(df_bil[(df_bil.Value.isnull() == True)|(df_bil.Value == 0)].index)

    return df_bil

#Vereinfachte Darstellung von Meldern in neuer Spalte "Melder":
def donor_short(df):
  df["Melder"] = df["Donor Agency"]
  #Vereinfachung der Bundesländer zu einer Kategorie:
  searchstring = ["Bundesland", "Bundesländer"]
  df.loc[df["Donor Agency"].str.contains('|'.join(searchstring)) == True, ["Melder"]] = "Bundesländer"
  #Anwenden der verkürzten Melder-Namen per Mapping:
  df["Melder"] = df["Melder"].map(keys_donoragency_kurz)
  df.loc[df["Donor Agency"] == "Andere", ["Melder"]] = "Leistungen für Geflüchtete in Deutschland"

  return df

#Einlesen der multilateralen Dateien:
def reader_multi(string1, string2, string3):
  df_multi1 = pd.read_csv(string1)
  df_multi2 = pd.read_csv(string2)
  df_multi3 = pd.read_csv(string3)

  df_multi1["Value"] = df_multi1["Value"] * 0.8473 
  df_multi2["Value"] = df_multi2["Value"] * 0.8933
  df_multi3["Value"] = df_multi3["Value"] * 0.8775

  df_multi = pd.concat([df_multi1, df_multi2, df_multi3])
  df_multi = df_multi.drop_duplicates()

  #Anpassen der relevanten Spalten an Namen der bilateralen Dateien
  df_multi["YEAR"] = df_multi["TIME"]
  df_multi["Donor Agency"] = df_multi["Agency Name"]
  #Mappen der deutschen Bezeichnungen für Donor Agencies:
  df_multi["Donor Agency"] = df_multi["Donor Agency"].map(keys_donoragency_deutsch)
  #Rename columns:
  df_multi["Bi/Multi"] = "Multilateral"

  return df_multi
  
df_bil = reader('CRS 2018 data.txt', 'CRS 2019 data.txt', 'CRS 2020 data.txt')
df_multi = reader_multi("multi2018.csv", "multi2019.csv", "multi2020.csv")
df_ges = pd.concat([df_bil, df_multi])
df_ges = donor_short(df_ges)

df_ges = df_ges[["Donor Agency", "Recipient Name", "Income Group", "YEAR", "Donor Project ID", "Project title", "Purpose Code", "Melder",
                  "Region", "Continent", "Bi/Multi", "Channel of Delivery Name", "Channel Category Name", "FinanceType Name", "Value"]]

df_ges.to_csv("df_ges.csv", index=False)