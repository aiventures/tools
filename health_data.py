""" Util file that helps to transform data from my health app into a single data frame (to be used for insert into my XLS file) """
from datetime import datetime
import traceback
import pandas as pd
debug = False

def read_file(filepath,encoding='utf-8'):
    """ reads data as lines from file """
    lines = []
    try:
        with open(filepath,encoding=encoding) as fp:
            for line in fp:
                lines.append(line)
    except:
        print(f"Exception reading file {filepath}")
        print(traceback.format_exc())

    return lines

def get_health_tables_from_file(filepath):
    """ reads health tables from input file and returns them in an output dictionary """

    # only get relevant columns
    relevant_colums = ['Datum', 'Uhrzeit', 'Sys.', 'Dia.', 
                       'Puls',"MAD", 'Gewicht', 'BMI', 'Body fat', 
                       'Wasseranteil', 'Muskelanteil', 'Wert']

    lines = read_file(f)
    health_tables = {"BLUTDRUCK":[],"GEWICHT":[],"BLUTZUCKER":[]}
    health_indicators = health_tables.keys()
    health_indicator = ""
    column_title_line = False
    column_titles = []

    for line in lines:
        line = line.strip()
        if debug:
            print(line)		
        # process line containing table column names
        if column_title_line:
            column_title_line = False
            line = line.replace('"',"") # special case for certain columns
            column_titles = line.split(";")
            print(f"Columns Titles: {column_titles}\n")
            continue

        line_strip = line.replace('"', "")
        cols = line_strip.split(";")
        if debug:
            print("cols",cols)


        if cols[0] in health_indicators:
            health_table = health_tables[cols[0]]
            print(f"--- Health Indicator {cols[0]} ---")
            column_title_line = True
            continue         

        # try to interprete as date. If successful we have a data line
        try:
            cols[0] = datetime.strptime(cols[0],"%d.%m.%Y") 
        except (ValueError) as e:
            if debug:
                print(f"couldnt interprete {cols[0]} as date ")
            continue

        # build dictionary
        line_dict = dict(zip(column_titles,cols))
        #if debug:
        #    print("line_dict",line_dict)
        keys = list(filter(lambda k: k in relevant_colums, line_dict.keys()))
        if debug:
            print("keys",keys)		
        line_dict = dict(zip(keys,[line_dict[k] for k in keys]))
        if debug:
            print("line_dict",line_dict)
        health_table.append(line_dict)
    if debug:
        print("health_tables",health_tables)
    return health_tables

def get_health_df(filepath):
    health_tables = get_health_tables_from_file(filepath)
    df_out = None

    output_map = {}
    output_map_parts = {"BLUTZUCKER":{"Z [mg/dl]":"Wert"},
                        "GEWICHT":   {"G [KG]":"Gewicht","BMI [kg/m2]":"BMI","FETT [%]":"Body fat",
                                      "WASSER [%]":"Wasseranteil","MUSKEL [%]":"Muskelanteil"},
                        "BLUTDRUCK": {"HzSYS":"Sys.","HzDia":"Dia.","HzPuls":"Puls","HzMAD":"MAD"}}
    fields_parts = {"BLUTZUCKER":["Wert"],
                    "GEWICHT":["Gewicht","BMI","Body fat","Wasseranteil","Muskelanteil"],
                    "BLUTDRUCK":["Sys.","Dia.","Puls","MAD"]}

    fields = []

    for health_table_type,health_table in health_tables.items():
        print(f"--- Table {health_table_type} ---")    
        if len(health_table) == 0:
            print(f"TABLE {health_table_type} IS EMPTY, will be skipped")
            continue
        
        output_map.update(output_map_parts[health_table_type])
        fields.extend(fields_parts[health_table_type])

        # convert into data frame
        df = pd.DataFrame(health_table)
        print(f" Shape {df.shape}")
        df.set_index('Datum', inplace=True)     

        # create or append dataframe columns
        if df_out is None:
            df_out = df
        else:
            df_out = pd.merge(left=df_out,right=df,how="outer",on="Datum")        

    # now we have all data in a single data frame, however it is required to condense rows as there are
    # duplicates for one day ...

    df_out.sort_index(inplace=True)

    # relevant data fields
    #fields=["Sys.","Dia.","Puls","MAD","Gewicht","BMI","Body fat","Wasseranteil","Muskelanteil","Wert"]
    df2 = df_out[fields]
    # replace decimal symbol / convert to numbers
    df2 = df2.replace(',','.',regex=True).apply(pd.to_numeric)

    # interpolate values, resample to daily basis
    df2 = df2.interpolate().resample('D').mean()

    # replace a percentage columns by real percentages
    percentage_list = ["Body fat","Wasseranteil","Muskelanteil"]
    df3 = df2.apply(lambda col: col/100 if col.name in percentage_list else col)

    # build the output df in correct order
    df4 = df3[[]]
    for trg,src in output_map.items():
        df4 = pd.concat([df4,df3[src]],axis=1)

    df4.columns = output_map.keys()
    # get the day difference between rows
    df4 = df4.reset_index()
    df4["Datum_DIFF"] = df4["Datum"].diff().dt.days

    return df4

def write_health_xls(filepath_in,filepath_xls):
    """ export to xls """
    df = get_health_df(filepath_in)
    df.to_excel(filepath_xls)
    print(f"\nHeatlth Data written to file:", filepath_xls)
    return df

# set paths for csv and output xls
f = r"C:\<path>\HealthManagerApp_DataExport.csv"
f_xls = r"C:\<path>\HealthManagerAppData.xls"

df = write_health_xls(f,f_xls)
df.head()

input("--- Press Key To Finish ---")