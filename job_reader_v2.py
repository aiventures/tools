""" reads job profiles from a text file, specification
    - reads line by line, duplicates possible and no dedicated sort order necessary
    - empty line is taken as separator between job descriptions
    - interpretes lines as Job Title (looking for '(m/w/d)' signature ), 
      company (looking for AG,SE,GmbH and NN in line) and company location (after comma),
      a company rating (1 digit, 2 decimals number at end of line), and salary range
      (thousand separator, line ending with € symbol ) and psoting date
    - example
      4.10.2019
      <Job Title> (m/w/d)
      <Company SE>, <Location>
      51.345 - 160.000€
      ? ? ? 3,45
      translates in dictionary:
      {"job":<Job Title>,"company":<Company SE>,"location": <Location>,
            "rating":3,45,"salary_min":51000,"salary_max":160000,"date":2019-10-4}
    - for regex terms refer to regex attributes in code
"""
import os
import re
import datetime
from functools import reduce
import hashlib

city_list=["Stuttgart","Karlsruhe","Mannheim","Heidelberg","Heilbronn","Fußgönheim","Neckarsulm","Pforzheim",
           "Renningen","Ludwigshafen am Rhein","Speyer","Walldorf","Sankt Leon-Rot","Frankfurt am Main","citynn"]

def get_hash_version(lines):
    """ calculates a hash string of selected dict fields """
    hash_fields = ["job","company","location"]
    seed = str(datetime.datetime.utcnow())

    for line in lines:
        for field in hash_fields:
            if isinstance(line[field],str):
                line[field] = hashlib.md5((seed+line[field]).encode())
    return lines

# finds out if one item in list is contained in s
# contains at least one extension
def contains(s:str,substrings:list):
    l = list(map(lambda i:i in s,substrings))
    return reduce(lambda a,b:a or b,l)

def get_jobtitles():
    """ list of jobtitles """
    jobtitles = [ "scientist", "engineer", "entwickler", "mathematician", "expert", 
                  "consultant", "berater", "ingenieur", "developer", "lead"]
    return jobtitles

def read_file_chunks(filepath, debug=False):
    """reads file chunks
       - reads line by line, duplicates possible and no dedicated sort order necessary
       - empty line is taken as separator between job descriptions
       - dates in separate lines will be detected
    """

    if not os.path.isfile(filepath):
        print("File path {} does not exist. Exiting...".format(filepath))
        return None

    chunks = []
    chunk = []
    d = datetime.datetime.now()
    last_line = ""
    idx_last = 0
    with open(filepath) as fp:    
        for idx,line in enumerate(fp):
            s = line.strip()

            if len(s) > 0:
                # check for date
                regex = r"(\d+)\.(\d+)\.(\d+)"
                date_parts = re.findall(regex,s)
                if len(date_parts) == 1 and len(date_parts[0]) == 3:
                    #reverse list to get order for datetime 
                    yyyy_mm_dd = list(map(int,date_parts[0]))[::-1] 
                    d = datetime.date(*yyyy_mm_dd)
                    continue
                else:
                    # last line was empty => append old one, create new chunk
                    if len(last_line) == 0:
                        chunk_dict = {}
                        chunk_dict["date"] = d
                        chunk_dict["line"] = idx_last+1
                        idx_last = idx
                        chunk_dict["chunk"] = chunk                        
                        if len(chunk) > 0:
                            chunks.append(chunk_dict)
                        chunk = [s]
                    # append data to new chunk / ignore duplicates
                    else:
                        if s not in chunk:
                            chunk.append(s)

            last_line = s

    return chunks 

def get_regex_dict():
    """ returns list of applied regex search patterns, an entry for a job offering 
        consists of multiple lines assumed are some search patterns. for definition 
        check comments in code of this function """

    # --- SALARY RANGE ---
    # regex specification for salary range (line ends with € symbol)
    # line is of pattern "(#)##).000 - ((#)##).000 €"  #: Digit (#) optional
    # extract the min and max numbers before the period
    regex_salary = {r"salary":r"(\d+)\.\d{3}[^0-9]*(\d+)\.\d{3}.*"}

    # --- COMPANY RATING ---
    # regex specification for rating
    # line is of pattern "? ? ? ? ?#,##"  #: Digit
    # extract the numbers andf convert it to float
    regex_rating = {r"rating":r"(\d,\d{2})$"}

    # different rating regex
    # 3,74 3.5 von 5 Sternen
    regex_rating2 =  {r"rating2":r"^(\d,\d{2}).*Sternen$"}

    # --- JOB DESCRIPTION ---
    # regex specification for job position extraction
    # line is of pattern "<job description> (..m..) Contains parentheses with m
    # extract <job description>
    regex_job = {r"job":r"(.*)\(.*m.*\)"}

    # --- COMPANY NAME AND LOCATION ---
    # regex specification for company extraction and location
    # line is of pattern "<company> [GmbH|SE|AG|Co], <location>
    # extract (<company> [...]) and location
    regex_company = {r"company":r"(.*GmbH.*|.*AG|.*NN|.*SE|.*Co|.*KG|.*Deutschland),(.*)"} 
    regex_company_only = {r"company_only":r"(.*GmbH.*|.*AG|.*NN|.*SE|.*Co|.*KG|.*Deutschland)"} 

    # --- COMPANY NAME AND LOCATION ---
    # regex specification for companies with known locations
    # line is of pattern "<company> [GmbH|SE|AG|Co], <location>
    # extract (<company> [...]) and location
    # location string
    s_locations = r"(.*), (" +"|".join(city_list)+")"
    regex_company_loc = {r"company_loc":s_locations}


    return {**regex_salary, **regex_rating, **regex_rating2, **regex_job, 
            **regex_company_only, **regex_company, **regex_company_loc}

def get_new_job_dict():
    """returns empty result dictionary, used as data template"""    
    empty = {"job":None,"company":None,"location":None,
           "rating":None,"salary_min":None,"salary_max":None,"date":None}
    return empty.copy()

def get_job_list(job_chunks,debug=False):
    """analyzes lines belonging to a job profile and extracts data depending on 
       data signature irrespective of order"""

    job_list = []
    job_regex = get_regex_dict()
    descriptors = job_regex.keys()
    job_dict_empty = get_new_job_dict()
    job_titles = get_jobtitles()

    for job_chunk_dict in job_chunks:
        job_dict = job_dict_empty.copy()
        job_dict["date"] = job_chunk_dict["date"]
        job_dict["line"] = job_chunk_dict["line"]
        job_chunks = job_chunk_dict.get("chunk",None)
        if job_chunks is None:
            continue
        for job_chunk in job_chunks:

            # check for job title 
            if ((contains(job_chunk.lower(),job_titles)) and (not job_dict["job"])):
                job_dict["job"] = job_chunk
                continue
            
            # check for location
            if job_chunk in city_list:
                job_dict["location"] = job_chunk
                continue

            # check for other segments
            for descriptor in descriptors:
                regex = job_regex[descriptor]
                search_result = re.findall(regex,job_chunk)

                if len(search_result) is not 0:
                    if debug is True:
                        print(f"descriptor: {descriptor}, regex: {regex}, result: {search_result}")                         
                    if (( descriptor == "job") and (not job_dict["job"])):
                        job_dict[descriptor] = search_result[0].strip()
                    elif descriptor == "company_only":
                        job_dict["company"] = search_result[0].strip()
                    elif descriptor == "company":
                        job_dict[descriptor] = search_result[0][0].strip()
                        job_dict["location"] = search_result[0][1].strip()               
                    elif descriptor == "company_loc":
                        job_dict["company"] = search_result[0][0].strip()
                        job_dict["location"] = search_result[0][1].strip()                             
                    elif descriptor == "rating":                
                        job_dict[descriptor] = float(search_result[0].replace(',','.'))              
                    elif descriptor == "rating2":                
                        job_dict["rating"] = float(search_result[0].replace(',','.'))                            
                    elif descriptor == "salary":
                        job_dict["salary_min"] = int(search_result[0][0])*1000
                        job_dict["salary_max"] = int(search_result[0][1])*1000        

        if job_dict.get("job",None) is not None:
            job_list.append(job_dict)
    return job_list    

def read_jobs_list(filepath,debug=False,erroneous=None,hashcells=False):
    """reads job descriptions from textfile and transforms it to data dictionary
       for detailed specs check method get_regex_dict 
       erroneous: None (No effect), True (only erroneous items)
       False (only correct items)       
    """
    attrib_list = ['job', 'company', 'location']
    filtered_list = []
    job_chunks_list = read_file_chunks(filepath)
    job_list = get_job_list(job_chunks_list,debug)

    if hashcells:
        job_list = get_hash_version(job_list)

    if erroneous is None:
        return job_list

    for entry in job_list:
        # check for errors
        error_list = list(map(lambda a:entry[a] is None,attrib_list))
        # at least one error needs to occur
        has_error = reduce(lambda e1,e2: e1 or e2,error_list)

        # return entry
        if has_error and erroneous:
            filtered_list.append(entry)
        elif not ( has_error or erroneous ):
            filtered_list.append(entry)

    return filtered_list
