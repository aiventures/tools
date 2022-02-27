""" 
    Module to calculate cumulated sums of key figures given in ETF List 
    Usage
    p         = r'<path>\\'   path to directory of ISIN Information files (ending with double backslash)
    prt       = r'<path to ETF csv file>'
    isin_list = [<list of ISIN files point to <isin>.txt files"]
    Get all portfolio infos and values in a single dataframe:
    df_etf = get_etf_df(p,prt,isin_list)

"""

import pandas as pd
import numpy as np
import pprint
import re
from functools import reduce

PREFIX = {"Stammdaten":"M_","Kosten":"C_","Positionen":"P_","Länder":"L_","Branchen":"B_"}
DUPLICATES = ["Sonstige"]
PREFIX_PORTFOLIO = "PRT_"

# prefix pattern: anything preceding an underscore
REGEX_REPLACE_PREFIX = re.compile("^(\w+_)",re.IGNORECASE)
VALUE_PREFIX = {"value_current":"VC_","value_invest":"VI_","value_change":"VD_"}
VALUE_COLUMN = {"value_current":"PRT_Value","value_invest":"PRT_ValueInvest","value_change":"PRT_ValueChange"}
PERCENTAGE_PREFIX = {"value_current":"PC_","value_invest":"PI_","value_change":"PD_"}
PERCENTAGE_COLUMN = {"value_current":"PCT_Value","value_invest":"PCT_ValueInvest","value_change":"PCT_ValueChange"}

# consolidate similar columns into one
MERGE_COLUMNS = {"B_Konsumgüter":["Basiskonsumgüter","Gebrauchsgüter","Nicht-Basiskonsumg","Konsum"],
                 "B_Finanzen":["Finanz"],
                 "B_Gesundheit":["Gesundheit"],
                 "B_ElektrischeAusrüstung":["Elektr. Ausrüstung"],
                 "B_Halbleiter":["Halbleiter"],
                 "B_Betriebsstoffe":["Betriebsstoffe"],
                 "B_IT":["Information","Internet","Systemsoftware","Anwendungssoftware","Hardware",
                        "Datenverarbeitung","IT Consulting"],
                 "B_Kommunikation":["Kommunikation","Telekommunikation"],
                 "B_Material":["Material"],
                 "L_Großbritannien":["Großbritannien"],
                 "P_Accenture":["Accenture"],
                 "P_ASML":["ASML"],
                 "P_Alphabet":["Alphabet"],
                 "P_Amazon":["Amazon"],
                 "P_Apple":["Apple"],
                 "P_Berkshire Hathaway":["Berkshire"],
                 "P_Facebook":["Facebook","Meta\W"],
                 "P_Nvidia":["Nvidia"],
                 "P_Visa":["Visa"]
                }

def read_file(f:str)->list:
    """ reading UTF8 txt File """
    lines = []
    try:
        with open(f,encoding="utf-8") as fp:    
            for line in fp:
                line = line.strip()
                if len(line) == 0:
                    continue
                lines.append(line)
    except:
        print(f"Exception reading file {f}")
        print(traceback.format_exc())
    return lines

def get_key_value_dict(lines:list,categories:list)->dict:
    # get segments belonging to one category
    # idx = [lines.index(idx)+1 for idx in categories]
    idx = []
    for category in categories:
        try:
            current_idx = lines.index(category)+1 
            idx.append(current_idx)
        except ValueError as e:
            print(f"Category {category} is not in list")
            
    
    idx.append(len(lines)+1)
    out_dict = {}    
    for n,i in enumerate(idx[:-1]):
        category = categories[n]
        idx_from = idx[n]
        idx_to = idx[n+1] - 1
        items = lines[idx_from:idx_to]
        entries = {}
        # assumption key value pairs in separate lines
        for j,keyvalue in enumerate(items[::2]):
            key = items[2*j]
            value = items[2*j+1]
            # transformation: currently only convert percentages
            if "%" in value:
                value = value.replace('%','').replace(',','.').strip() + 'e-2'
                value = float(value)
            entries[key] = value
        out_dict[category] = entries
    return out_dict

def asfloat(s)->float:
    try:
        v = s.replace('€','').replace('Stk.','').replace(' %','E-2') \
             .strip() \
             .replace('.',"").replace(',','.')
        return float(v)
    except ValueError as e:
        return s

    
def get_portfolio_df(fp:str)->pd.DataFrame:
    """ uses subsembly banking csv format to create dataframe with values """
    # reading ansi csv with given decimals and delimiters
    df = pd.read_csv(fp, header=0, decimal=",", delimiter=";",encoding="ANSI")    
    # numerical columns
    n_cols = ['Quantity', 'PriceInvest','ValueInvest', 'PriceChange', 'ValueChange',
              'PriceChangePercent', 'PriceCurrent', 'Value']
    
    #columns to be dropped
    drop_cols = ["MaturityDate","InterestRate","BlockedUntilDate","InvestDate","AdditionalInfo","Invest","PriceInvestCurrency","Change"
                 ,"Current","PriceCurrentCurrency","ValueCurrent","ValueEuroCurrent"]
    df.drop(drop_cols,axis=1,inplace=True)                 

    for col in n_cols:
        df[col] = df[col].apply(asfloat)
    
    return df

def get_isin_factsheets(p:str,isin_list:list,output:bool=False)->dict:
    """ reading factsheets from key value text files """
    ISIN_INFO_DETAIL_URL = r"https://wertpapiere.ing.de/Investieren/Fonds/Fondsprofil/"
    categories = ["Stammdaten","Kosten","Positionen","Länder","Branchen"]
    isin_factsheet_dict = {}
    for isin in isin_list:
        url = ISIN_INFO_DETAIL_URL+isin    
        l = read_file(p+isin+".txt")#
        d = get_key_value_dict(l,categories)    
        d["url"] = url
        isin_factsheet_dict[isin] = d
    if output:
        pprint.PrettyPrinter(indent=2).pprint(isin_factsheet_dict)
    return isin_factsheet_dict

def get_factsheet_info(p:str,isin_list:list,output:bool=False)->dict:
    """ reads all attributes across isin lists """
    
    isin_facts_d = get_isin_factsheets(p,isin_list)

    fact_dict =  {"Branchen":{},"Länder":{},"Positionen":{}}
    for isin,facts in isin_facts_d.items():
        for fact_key,fact_values in fact_dict.items():        
            keys = list(facts[fact_key].keys())
            #print(isin,keys)
            current_dict = fact_dict[fact_key]
            for key in keys:                
                key_entry = current_dict.get(key,[])
                key_entry.append(isin)
                current_dict[key] = key_entry            


    for fact_key,fact_values in fact_dict.items():
        for fact_value_key,isin_list in fact_values.items():
            fact_dict[fact_key][fact_value_key]={"isin_list":isin_list,"num":len(isin_list)}
            
    if output:
        pprint.PrettyPrinter(indent=2).pprint(fact_dict)
        
    return fact_dict

def get_factsheet_df(p:str,isin_list:list,output:bool=False)->pd.DataFrame:
    """ reads factsheets and transforms it into a dataframe """    
    # reading factsheets as dictionary
    factsheets_d = get_isin_factsheets(p,isin_list,output=output)
    
    # flatten factsheets
    out_dict = {}
    for isin,factsheet_info in factsheets_d.items():
        flat_dict = {}
        for factsheet_info_key,factsheets in factsheet_info.items():
            prefix = PREFIX.get(factsheet_info_key,"")
            new_dict = {}
            if isinstance(factsheets,dict):
                keys_new = [(prefix+key) for key in factsheets.keys()]
                new_dict = dict(zip(keys_new,factsheets.values()))
            elif isinstance(factsheets,str):
                new_dict = {(prefix+factsheet_info_key):factsheets}
            flat_dict.update(new_dict)
        out_dict[isin] = flat_dict
         
    # convert to dataframe
    df_factsheet = pd.DataFrame(out_dict).transpose()
    df_factsheet = df_factsheet.reindex(columns=df_factsheet.columns.sort_values())
    
    # replace duplicate column titles
    df_columns = df_factsheet.columns
    for duplicate in DUPLICATES:
        for prefix in PREFIX.values():
            duplicate_key = prefix + duplicate
            if duplicate_key in df_columns:                
                df_factsheet = df_factsheet.rename(columns={duplicate_key:(duplicate_key+prefix.replace("_",""))})
    return df_factsheet

def read_etf_df(p:str,portfolio_csv:str,isin_list:list,output:bool=False)->pd.DataFrame:
    """ reads factsheet and portfolio info into one dataframe """
    df_portfolio = get_portfolio_df(portfolio_csv)
    df_portfolio = df_portfolio.set_index("ISIN")
    df_portfolio.columns = PREFIX_PORTFOLIO + df_portfolio.columns.values
    df_factsheet = get_factsheet_df(p,isin_list,output=output)
    df_portfolio = df_portfolio.join(df_factsheet, how='inner', sort=True)
    
    return df_portfolio

def replace_prefix(s:str,new_prefix="PRE_"):
    replace_s = REGEX_REPLACE_PREFIX.match(s)
    if replace_s:
        replace_s = s[:replace_s.span(0)[1]]
        s = s.replace(replace_s,new_prefix)
    return s

def consolidate_columns(df:pd.DataFrame,merge_columns:dict=MERGE_COLUMNS,output:bool=False)->pd.DataFrame:
    """ merge similar columns into one major column """
    # identify merge_columns                 
    merge_col_dict = {}
    columns = df.columns
    for col in columns:
        merge_cols = {}
        for merge_col,merge_conditions in merge_columns.items():
            # find matching column names 
            result = [(re.search(regex,col,re.IGNORECASE)!=None) for regex in merge_conditions]
            if reduce(lambda v1,v2: v1 or v2,result):
                merge_col_list = merge_col_dict.get(merge_col,[])
                merge_col_list.append(col)
                merge_col_dict[merge_col] = merge_col_list
    
    if output:
        print("--- Column Merge ---")        
        pprint.PrettyPrinter(indent=2).pprint(merge_col_dict)

    # merge columns in dataframe, add columns 
    # (results may be wrong, correct results only if only one consolidated columns contains values)
    for merge_col,merge_col_list in merge_col_dict.items():  
        df[merge_col] =  df[merge_col_list].sum(axis=1)
        if merge_col in merge_col_list:
            merge_col_list.remove(merge_col)
        df.drop(merge_col_list,axis=1,inplace=True)  
        
    # sort index
    df = df.reindex(columns=df.columns.sort_values())                    
    return df

def calculate_portfolio_values(df:pd.DataFrame,value_type:str="value_current",output:bool=False):
    """ calculate absolute portfolio values from portfolio """
    value_column = VALUE_COLUMN[value_type]
    prefix = VALUE_PREFIX[value_type]

    # get only columns containing numerical columns
    df_numerical = df.fillna(0).select_dtypes(include=[np.number])        
    values = df[value_column]
    # eliminate all portfolio related information
    drop_cols = [drop_col for drop_col in df_numerical.columns if drop_col.startswith(PREFIX_PORTFOLIO)]    
    df_numerical.drop(drop_cols,axis=1,inplace=True)  
    
    # get absolute values based on portfolio information
    df_values = df_numerical.mul(values,axis=0)
    # now get all column types with values
    column_types = list(PREFIX.values()).remove(PREFIX["Stammdaten"])

    column_types = list(PREFIX.values())
    column_types.remove(PREFIX["Stammdaten"])
    # get new column titles
    columns = [col for col in df.columns if (col[:2] in column_types)]    
    new_columns = [replace_prefix(col_name,new_prefix=prefix) for col_name in list(df_values.columns)]
    new_columns_dict = dict(zip(df_values.columns,new_columns))
    df_values = df_values.rename(columns=new_columns_dict)
    return df_values

def get_etf_df(p:str,prt:str,isin_list:list,output:bool=False)->pd.DataFrame:
    """ reads portfolio data and calculates etf dataframe with a couple of key figures  
        p: path to ISIN Data
        prt: path to portfolio csv (format as defined by banking software)
        isin_list: ISIN List to be read from p (filename needs to match <ISIN_LIST>.txt)
    """
    # get the main etf info dataframe
    df_portfolio = read_etf_df(p,prt,isin_list,output=output)
    # consolidate categories
    df2 = consolidate_columns(df_portfolio,output=False)    
    
    # calculate numerical values
    df_values = None
    perc_column_title_map = {}
    value_types = VALUE_PREFIX.keys()
    for value_type in value_types:
        df_value = calculate_portfolio_values(df_portfolio,value_type=value_type,output=False);
        if (df_values is not None):
            df_values = pd.concat([df_values,df_value],axis=1)
        else:
            df_values = df_value

        # get column titles percentage mapping 
        # print(df_value.columns)
        current_cols = df_value.columns
        current_prefix = VALUE_PREFIX[value_type]
        percent_prefix = PERCENTAGE_PREFIX[value_type]
        percent_cols =[(percent_prefix+c[len(current_prefix):]) for c in current_cols]
        # print(percent_cols)
        perc_column_title_map.update(dict(zip(current_cols,percent_cols)))

    # add value columns / calculate sum
    df_portfolio = df_portfolio.join(df_values, how='inner', sort=True)
    df_portfolio.loc["SUM"] = df_values.sum(numeric_only=True)

    # calculate / add percentages
    df_percentages = df_portfolio[df_values.columns].apply(lambda row: row / row["SUM"] ,axis=0)
    # rename percentage columns
    df_percentages=df_percentages.rename(columns=perc_column_title_map)
    df_portfolio = df_portfolio.join(df_percentages, how='inner', sort=True)    
    
    return df_portfolio