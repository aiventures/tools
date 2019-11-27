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
import sys
import os
import re
import datetime
from phpbb_scraper import persistence
from phpbb_scraper import html_converter

def read_jobs(filepath,debug=False):
    """reads job profiles from online applications, specification from given file path
       - reads line by line, duplicates possible and no dedicated sort order necessary
       - empty line is taken as separator between job descriptions
       - for interpretation of lines refer other methods
    """       
       
    if not os.path.isfile(filepath):
        print("File path {} does not exist. Exiting...".format(filepath))
        return None
    
    jobs = []    
    descriptions = []
    with open(filepath) as fp:    
        for line in fp:
            s = line.strip()
            if len(s) == 0:            
                if len(descriptions) > 0:
                    if debug is True:
                        print("---JOB DESCRIPTIONS---")
                        print(f"{descriptions}")
                    jobs.append(descriptions)
                descriptions = []
            else:
                descriptions.append(s)

    return jobs          

def get_regex_dict():
    """ returns list of applied regex search patterns, an entry for a job offering 
        consists of multiple lines assumed are some search patterns. for definition 
        check comments in code of this function """

    # --- SALARY RANGE ---
    # regex specification for salary range (line ends with € symbol)
    # line is of pattern "(#)##).000 - ((#)##).000 €"  #: Digit (#) optional
    # extract the min and max numbers before the period
    regex_salary = {r"salary":r"(\d+)\.\d{3}[^0-9]*(\d+)\.\d{3}.*€$"}

    # --- COMPANY RATING ---
    # regex specification for rating 
    # line is of pattern "? ? ? ? ?#,##"  #: Digit
    # extract the numbers andf convert it to float
    regex_rating = {r"rating":r"(\d,\d{2})$"}

    # --- JOB DESCRIPTION ---
    # regex specification for job position extraction
    # line is of pattern "<job description> (..m..) Contains parentheses with m
    # extract <job description>
    regex_job = {r"job":r"(.*)\(.*m.*\)"}

    # --- COMPANY NAME AND LOCATION ---
    # regex specification for company extraction and location
    # line is of pattern "<company> [GmbH|SE|AG], <location>
    # extract (<company> [...]) and location 
    regex_company = {r"company":r"(.*GmbH.*|.*AG|.*NN|.*SE),(.*)"}

    # --- POSTING DATE ---
    # regex specification for company date
    # line is of pattern ... DD.MM.YYYY ... (Date)
    # extract DD,MM,YYYY and generate datetime object 
    regex_date = {r"date":r"(\d+)\.(\d+)\.(\d+)"}    

    return {**regex_salary,**regex_rating,**regex_job,**regex_company,**regex_date}

def get_new_job_dict():
    """returns empty result dictionary, used as data template"""    
    empty = {"job":None,"company":None,"location":None,
           "rating":None,"salary_min":None,"salary_max":None,"date":None}
    return empty.copy()

def get_job_attribute_dict(job_description_lines,debug=False):
    """analyzes lines belonging to a job profile and extracts data depending on 
       data signature irrespective of order"""
    
    job_regex = get_regex_dict()
    descriptors = job_regex.keys()
    job_dict = get_new_job_dict()
    if debug is True:
        print("---JOB DESCRIPTION LINES------------")        
        print(job_description_lines)

    for job_description in job_description_lines:
        for descriptor in descriptors:
            regex = job_regex[descriptor]
            search_result = re.findall(regex,job_description)
            if len(search_result) is not 0:
                if debug is True:
                    print(f"descriptor: {descriptor}, regex: {regex}, result: {search_result}")                         
                if descriptor == "job":
                    job_dict[descriptor] = search_result[0].strip()
                elif descriptor == "company":
                    job_dict[descriptor] = search_result[0][0].strip()
                    job_dict["location"] = search_result[0][1].strip()               
                elif descriptor == "rating":                
                    job_dict[descriptor] = float(search_result[0].replace(',','.'))              
                elif descriptor == "salary":
                    job_dict["salary_min"] = int(search_result[0][0])*1000
                    job_dict["salary_max"] = int(search_result[0][1])*1000
                elif descriptor == "date":
                    date_parts = search_result
                    if len(date_parts) == 1 and len(date_parts[0]) == 3:
                        #reverse list to get order for datetime 
                        yyyy_mm_dd = list(map(int,date_parts[0]))[::-1] 
                        job_dict["date"] = datetime.date(*yyyy_mm_dd)

    if debug is True:
        print(f"job dictionary: {job_dict}")
    return job_dict  

def read_jobs_as_dict(filepath,debug=False):
    """reads job descriptions from textfile and transforms it to data dictionary
       for detailed specs check method get_regex_dict """
    jobs_as_lines =  read_jobs(filepath,debug=debug)
    jobs_as_dict = [get_job_attribute_dict(job_as_lines,debug=debug) for job_as_lines in jobs_as_lines ]
    return jobs_as_dict        


