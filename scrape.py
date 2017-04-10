import csv
import json
import os
import time

import bs4
import numpy as np
import pandas as pd
import requests

import config


def load_fits(directory=config.unkindness_fits_path):
    fit_list = []
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            fit_path = os.path.join(directory, filename)
            fit_list.append(fit_path)
        else:
            continue

    return fit_list


def create_dict(fit, item_type, item_name, item_count, system):
    
    return {'fit': fit,
            'item_type': item_type,
            'item_name': item_name,
            'item_count': item_count,
            'system': system}


def count_total(current_fit):
    count = []
    for system in config.unkindness_stock_master.keys():
        count.append((config.unkindness_stock_master[system][current_fit],
                      system))
    
    return count

def system_counts(df, assembled_dict, stock_dict, current_fit, current_type, current_item):
    for k in config.unkindness_stock_master.keys():
        df_assembled

def fits_dataframe(fit_list):
    columns = ['fit', 'item_type', 'item_name', 'item_count', 'system']
    df = pd.DataFrame(columns=columns)

    # Assess the stocks from each system
    assembled_dict, stock_dict = stock()

    for fit_path in fit_list:
        with open(fit_path, 'r') as f:
            fit = f.read()

        current_assembled = 0
        current_fit = ''
        current_type = 'ship'
        current_item = ''
        current_line = ['line', 'line', 'line', 'line']

        for i, line in enumerate(fit.splitlines()):
            current_line = current_line[1:]
            current_line.extend([line])
            current_set = set(current_line)
            if i == 0:
                current_fit = line
                current_item = line.split(',')[0][1:]
                count_list = count_total(current_fit)
                for item_count, system in count_list:
                    df = df.append([create_dict(current_fit, current_type, current_item, item_count, system)])
            elif i == 1:
                current_type = 'module'
            elif len(current_set) == 1:
                if list(current_set)[0] == '':
                    current_type = 'ammo'

            if i!= 0 and line != '':
                if current_type == 'ammo':
                    current_item, item_count = line.rsplit(' x')
                    item_count = int(item_count)
                    item_count *= count_total(current_fit)
                else:
                    current_item = line
                    count_list = count_total(current_fit)
                # Loop through each of systems adding rows for the unique item's counts
                for item_count, system in count_list:
                    df = df.append([create_dict(current_fit, current_type, current_item, item_count, system)])
            else:
                pass
    
    return df


def stock():
    df_assembled = pd.DataFrame(columns=config.ship_hanger_columns)
    df_stock = pd.DataFrame(columns=config.ship_hanger_columns)
    # Loop through systems where fits are needed.
    for system in config.unkindness_stock_master.keys():
        df_total = pd.DataFrame()
        # Loop through each of the hangers
        for hanger in ['ships', 'items']:
            with open('/home/bitcloudo/eclipse/stock/unkindness/{}_{}.txt'.format(system, hanger)) as f:
                reader = csv.reader(f, delimiter="\t")
                d = list(reader)
            df_temp = pd.DataFrame(d, columns=config.ship_hanger_columns)
            df_temp['system'] = system
            df_total = df_total.append(df_temp)
        # Any items/ships that have been assembled, ie Fit ships, are stored here
        df_assembled = df_assembled.append(df_total[df_total['quantity'] == ''])
        # Any items/ships that have not been assembled, ie backstock items, are stored here
        df_stock = df_stock.append(df_total[df_total['quantity'] != ''])

    return df_assembled, df_stock


def merge_df(df_grouped, df_stock):
    for system in config.unkindness_stock_master.keys():
        stock(system)



def main():
    fit_list = load_fits()
    df = fits_dataframe(fit_list)
    df_grouped = df.groupby(['system', 'item_type', 'item_name'], as_index=False).sum()
    
    df_grouped = df_grouped[['system', 'item_type', 'item_name', 'item_count']].sort_values(['system', 'item_type', 'item_name', 'item_count'], ascending=[True, False, True, False])

    #df_combined = merge_df(df_grouped, df_stock)
    
    # Join ship stock
    #df_grouped.merge(df_grouped, left_on='item_name', right_on='Name', how='left')

    writer = pd.ExcelWriter('fit_summary.xlsx', engine='xlsxwriter')
    df_grouped.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    
    print "Complete!!!"
