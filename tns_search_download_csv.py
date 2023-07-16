#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Avgust 2021

Developed and tested on:

- Linux 20.04 LTS
- Windows 10
- Python 3.8 (Spyder 4)

@author: Nikola Knezevic ASTRO DATA
"""

import datetime
import os
import requests
import json
import time

#----------------------------------------------------------------------------------

#TNS                  = "sandbox.wis-tns.org"
TNS                  = "www.wis-tns.org"
url_tns_search       = "https://" + TNS + "/search"

TNS_BOT_ID           = "YOUR_BOT_ID_HERE"
TNS_BOT_NAME         = "YOUR_BOT_NAME_HERE"
TNS_API_KEY          = "YOUR_BOT_API_KEY_HERE"

TNS_UID              = "YOUR_USER_ID"
TNS_USER_NAME        = "YOUR_USER_NAME"

USER_OR_BOT          = "Here put 'user' or 'bot' depending on who is sending requests."

# all possible parameters for building TNS search url
URL_PARAMETERS       = ["discovered_period_value", "discovered_period_units", "unclassified_at", "classified_sne", "include_frb",
                        "name", "name_like", "isTNS_AT", "public", "ra", "decl", "radius", "coords_unit", "reporting_groupid[]",
                        "groupid[]", "classifier_groupid[]", "objtype[]", "at_type[]", "date_start[date]",
                        "date_end[date]",  "discovery_mag_min", "discovery_mag_max", "internal_name", "discoverer", "classifier",
                        "spectra_count", "redshift_min", "redshift_max", "hostname", "ext_catid", "ra_range_min", "ra_range_max",
                        "decl_range_min", "decl_range_max", "discovery_instrument[]", "classification_instrument[]",
                        "associated_groups[]", "official_discovery", "official_classification", "at_rep_remarks", "class_rep_remarks",
                        "frb_repeat", "frb_repeater_of_objid", "frb_measured_redshift", "frb_dm_range_min", "frb_dm_range_max",
                        "frb_rm_range_min", "frb_rm_range_max", "frb_snr_range_min", "frb_snr_range_max", "frb_flux_range_min",
                        "frb_flux_range_max", "format", "num_page"]

url_parameters       = {"include_frb" : "1", "at_type[]" : "5", "reporting_groupid[]" : "86", 
                        "format" : "tsv", "num_page" : "206", "frb_repeat" : }

# Merge retrieved entries into single CSV/TSV file (0 --> NO, 1 --> YES)
MERGE_TO_SINGLE_FILE  = "1"

# external http errors
ext_http_errors       = [403, 500, 503]
err_msg               = ["Forbidden", "Internal Server Error: Something is broken", "Service Unavailable"]

#----------------------------------------------------------------------------------

def set_bot_tns_marker():
    tns_marker = 'tns_marker{"tns_id": "' + str(TNS_BOT_ID) + '", "type": "bot", "name": "' + TNS_BOT_NAME + '"}'
    return tns_marker

def set_user_tns_marker():
    tns_marker = 'tns_marker{"tns_id": "' + str(TNS_UID) + '", "type": "user", "name": "' + TNS_USER_NAME + '"}'
    return tns_marker

def is_string_json(string):
    try:
        json_object = json.loads(string)
    except Exception:
        return False
    return json_object

def response_status(response):
    json_string = is_string_json(response.text)
    if json_string != False:
        status = "[ " + str(json_string['id_code']) + " - '" + json_string['id_message'] + "' ]"
    else:
        status_code = response.status_code
        if status_code == 200:
            status_msg = 'OK'
        elif status_code in ext_http_errors:
            status_msg = err_msg[ext_http_errors.index(status_code)]
        else:
            status_msg = 'Undocumented error'
        status = "[ " + str(status_code) + " - '" + status_msg + "' ]"
    return status

def print_response(response, page_num):
    status = response_status(response)
    if response.status_code == 200:     
        stats = 'Page number ' + str(page_num) + ' | return code: ' + status + \
                ' | Total Rate-Limit: ' + str(response.headers.get('x-rate-limit-limit')) + \
                ' | Remaining: ' + str(response.headers.get('x-rate-limit-remaining')) + \
                ' | Reset: ' + str(response.headers.get('x-rate-limit-reset') + ' sec')
    
    else:       
        stats = 'Page number ' + str(page_num) + ' | return code: ' + status        
    print (stats)

def get_reset_time(response):
    # If any of the '...-remaining' values is zero, return the reset time
    for name in response.headers:
        value = response.headers.get(name)
        if name.endswith('-remaining') and value == '0':
            return int(response.headers.get(name.replace('remaining', 'reset')))
    return None        

# function for searching TNS with specified url parameters
def search_tns():
    #--------------------------------------------------------------------
    # extract keywords and values from url parameters
    keywords = list(url_parameters.keys())
    values = list(url_parameters.values())
    #--------------------------------------------------------------------
    # flag for checking if url is with correct keywords
    wrong_url = False
    # check if keywords are correct
    for i in range(len(keywords)):
        if keywords[i] not in URL_PARAMETERS:
            print ("Unknown url keyword '"+keywords[i]+"'\n")
            wrong_url = True
    # check flag
    if wrong_url == True:
        print ("TNS search url is not in the correct format.\n")
    #--------------------------------------------------------------------
    # else, if everything is correct
    else:
        # current date and time
        current_datetime = datetime.datetime.now()
        current_date_time = current_datetime.strftime("%Y%m%d_%H%M%S")
        # current working directory
        cwd = os.getcwd()        
        # create searched results folder
        if MERGE_TO_SINGLE_FILE == 0:
            tns_search_folder = "tns_search_data_" + current_date_time
            tns_search_folder_path = os.path.join(cwd, tns_search_folder)
            os.mkdir(tns_search_folder_path)
            print ("TNS searched data folder /" + tns_search_folder + "/ is successfully created.\n")            
        # file containing searched data
        if "format" in keywords:
            extension = "." + url_parameters["format"]
        else:
            extension = ".txt"
        tns_search_file = "tns_search_data_" + current_date_time + extension
        tns_search_file_path = os.path.join(cwd, tns_search_file)
        #--------------------------------------------------------------------
        # build TNS search url
        url_par = ['&' + x + '=' + y for x, y in zip(keywords, values)]
        tns_search_url = url_tns_search + '?' + "".join(url_par)
        #--------------------------------------------------------------------
        # page number
        page_num = 0
        # searched data
        searched_data = []
        # go trough every page
        while True:
            # url for download
            url = tns_search_url + "&page=" + str(page_num)
            # TNS marker
            if USER_OR_BOT == 'bot':
                tns_marker = set_bot_tns_marker()
            else:
                tns_marker = set_user_tns_marker()
            # headers
            headers = {'User-Agent': tns_marker}
            # downloading file using request module
            response = requests.post(url, headers=headers, stream=True)
            # chek if response status code is not 200, or if returned data is empty
            if (response.status_code != 200) or (len((response.text).splitlines()) <= 1):
                if response.status_code != 200:
                    print ("Sending download search request for page num " + str(page_num + 1) + "...")
                    print_response(response, page_num + 1)
                break            
            print ("Sending download search request for page num " + str(page_num + 1) + "...")
            # print status code of the response
            print_response(response, page_num + 1)
            # get data
            data = (response.text).splitlines()
            # create file per page
            if MERGE_TO_SINGLE_FILE == 0:
                tns_search_f = "tns_search_data_" + current_date_time + "_part_" + str(page_num + 1) + extension
                tns_search_f_path = os.path.join(tns_search_folder_path, tns_search_f)
                f = open(tns_search_f_path, 'w')
                for el in data:
                    f.write(el + '\n')
                f.close() 
                if len(data) > 2:
                    print ("File '" + tns_search_f + "' (containing " + str(len(data) - 1) + " rows) is successfully created.\n")                     
                else: 
                    print ("File '" + tns_search_f + "' (containing 1 row) is successfully created.\n")
            else:
                print ("")
            # add to searched data
            if page_num == 0:
                searched_data.append(data)
            else:
                searched_data.append(data[1 : ])
            # check reset time
            reset = get_reset_time(response)
            if reset != None:
                # Sleeping for reset + 1 sec
                print("\nSleep for " + str(reset + 1) + " sec and then continue...\n") 
                time.sleep(reset + 1)
            # increase page num
            page_num = page_num + 1
        #--------------------------------------------------------------------
        # if there is searched data, write to file
        if searched_data != []:            
            searched_data = [j for i in searched_data for j in i]            
            if MERGE_TO_SINGLE_FILE == 1:
                f = open(tns_search_file_path, 'w')
                for el in searched_data:
                    f.write(el + '\n')
                f.close()
                if len(searched_data) > 2:
                    print ("\nTNS searched data returned " + str(len(searched_data) - 1) + " rows. File '" + \
                           tns_search_file + "' is successfully created.\n")
                else: 
                    print ("\nTNS searched data returned 1 row. File '" + tns_search_file + "' is successfully created.\n")            
            else:                
                if len(searched_data) > 2:
                    print ("TNS searched data returned " + str(len(searched_data) - 1) + " rows in total.\n")
                else: 
                    print ("TNS searched data returned 1 row in total.\n")
        else:
            if MERGE_TO_SINGLE_FILE == 1:
                print ("")
            print ("TNS searched data returned empty list. No file(s) created.\n")
            # remove empty folder
            if MERGE_TO_SINGLE_FILE == 0:
                os.rmdir(tns_search_folder_path)
                print ("Folder /" + tns_search_folder + "/ is removed.\n")

#----------------------------------------------------------------------------------
"""
# EXAMPLE 1 (for CHIME FRBs, 50 per page)
TNS_BOT_ID           = "YOUR_BOT_ID_HERE"
TNS_BOT_NAME         = "YOUR_BOT_NAME_HERE"
TNS_API_KEY          = "YOUR_BOT_API_KEY_HERE"
USER_OR_BOT          = "bot"
url_parameters       = {"include_frb" : "1", "at_type[]" : "5", "reporting_groupid[]" : "86", 
                        "format" : "tsv", "num_page" : "50"}
MERGE_TO_SINGLE_FILE = 1
search_tns()
"""

"""
# EXAMPLE 2 (for classified SNe over the last 2 months, 100 per page)
TNS_UID              = "YOUR_USER_ID"
TNS_USER_NAME        = "YOUR_USER_NAME"
USER_OR_BOT          = "user"
url_parameters       = {"discovered_period_value" : "2", "discovered_period_units" : "months", 
                        "classified_sne" : "1", "format" : "csv", "num_page" : "100"}
MERGE_TO_SINGLE_FILE = 1
search_tns()
"""

"""
# EXAMPLE 3 (for classified SNe over the last 3 months, 20 per page)
TNS_UID              = "YOUR_USER_ID"
TNS_USER_NAME        = "YOUR_USER_NAME"
USER_OR_BOT          = "user"
url_parameters       = {"discovered_period_value" : "3", "discovered_period_units" : "months", 
                        "classified_sne" : "1", "format" : "csv", "num_page" : "20"}
MERGE_TO_SINGLE_FILE = 0
search_tns()
"""
#----------------------------------------------------------------------------------

