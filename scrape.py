import json
import os
import time

import bs4
import numpy as np
import pandas as pd
import requests
import bs4


def scrape_general(save_copy=False):
    
    link = "https://zkillboard.com/kills/nullsec/"
    # Go to the link and get the html as a string
    html = requests.get(link)
    
    # If not error
    if html.status_code != 200:
        print "Status error returned: 200"


def load_fits(directory='/home/bitcloudo/eclipse/fits/unkindness/'):
    fit_list = []
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            fit_path = os.path.join(directory, filename)
            fit_list.append(fit_path)
        else:
            continue

    return fit_list

def create_dict(fit, item_type, item_name, item_count):
    
    return {'fit': fit, 'item_type': item_type, 'item_name': item_name, 'item_count': item_count}

def fits_dataframe(fit_list):
    current_fit = ''
    current_type = 'ship'
    current_item = ''
    current_line = ['line', 'line', 'line', 'line']
    columns = ['fit', 'item_type', 'item_name', 'item_count']
    df = pd.DataFrame(columns=columns)

    for fit_path in fit_list:
        with open(fit_path, 'r') as f:
            fit = f.read()

        current_fit = ''
        current_type = 'ship'
        current_item = ''
        current_line = ['line', 'line', 'line', 'line']
        columns = ['fit', 'item_type', 'item_name', 'item_count']

        for i, line in enumerate(fit.splitlines()):
            current_line = current_line[1:]
            current_line.extend([line])
            current_set = set(current_line)
            if i == 0:
                current_fit = line
                current_item = line.split(',')[0][1:]
                item_count = 1
                df = df.append([create_dict(current_fit, current_type, current_item, item_count)])
            elif i == 1:
                current_type = 'module'
            elif len(current_set) == 1:
                if list(current_set)[0] == '':
                    current_type = 'ammo'

            if i!= 0 and line != '':
                if current_type == 'ammo':
                    current_item, item_count = line.rsplit(' x')
                else:
                    current_item = line
                    item_count = 1
                df = df.append([create_dict(current_fit, current_type, current_item, item_count)])
            else:
                pass
    
    return df

def main():
    fit_list = load_fits()
    df = fits_dataframe(fit_list)
    df_grouped = df.groupby(['item_type', 'item_name'], as_index=False).sum()
    
    df_grouped = df_grouped[['item_type', 'item_name', 'item_count']].sort_values(['item_type', 'item_name', 'item_count'], ascending=[False, True, False])
    writer = pd.ExcelWriter('fit_summary.xlsx', engine='xlsxwriter')
    df_grouped.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    
    print "Complete!!!"
