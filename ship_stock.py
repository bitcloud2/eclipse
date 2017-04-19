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


def count_total(current_fit, clean_dict=config.unkindness_stock_master):
    count = []
    for system in clean_dict.keys():
        count.append((clean_dict[system][current_fit],
                      system))
    
    return count

def fits_dataframe(fit_list, clean_dict):
    columns = ['fit', 'item_type', 'item_name', 'item_count', 'system']
    df = pd.DataFrame(columns=columns)

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
            current_set = set(current_line[1:])
            if i == 0:
                current_fit = line
                current_item = line.split(',')[0][1:]
                count_list = count_total(current_fit, clean_dict)
                for item_count, system in count_list:
                    df = df.append([create_dict(current_fit, current_type, current_item, item_count, system)])
            elif i == 1 and current_type != 'ammo':
                current_type = 'module'
            elif len(current_set) == 1:
                if list(current_set)[0] == '':
                    current_type = 'ammo'

            if i!= 0 and line != '':
                if current_type == 'ammo':
                    current_item, ammo_count = line.rsplit(' x')
                    ammo_count = int(ammo_count)
                    #ammo_count *= count_total(current_fit, clean_dict)
                else:
                    current_item = line
                    count_list = count_total(current_fit, clean_dict)
                # Loop through each of systems adding rows for the unique item's counts
                for item_count, system in count_list:
                    if current_type == 'ammo':
                        item_count *= ammo_count
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

def current_needs(df_assembled):
    df_stock_master = pd.DataFrame(config.unkindness_stock_master)
    df_stock_master['ship'] = map(lambda line: line.split(',')[0][1:], df_stock_master.index)
    df_stock_master['fit'] = df_stock_master.index
    df_assembled_ships = df_assembled[['name', 'system']]
    df_assembled_ships['stock_count'] = 1
    # Add column for each system at attribute stock_count as values
    for system in df_assembled_ships['system'].unique():
        df_assembled_ships.ix[df_assembled_ships['system'] == system, system] = \
                df_assembled_ships[df_assembled_ships['system'] == system]['stock_count']

    df_assembled_group = df_assembled_ships.groupby(['name', 'system'], as_index=False).sum()
    
    df_combined = df_stock_master.merge(df_assembled_group,
                                        left_on=['ship'],
                                        right_on=['name'],
                                        suffixes=('', '_stock'),
                                        how='left')

    df_combined.fillna(0, inplace=True)

    # Loop through systems adding the stock in for each fo them
    # TODO: Make work for multiple fits of the same ship
    for system2 in df_assembled_ships['system'].unique():
        df_combined[system2] = df_combined[system2] - df_combined[system2 + '_stock']
        df_combined[system2] = df_combined[system2].astype(int)
        df_combined.drop([system2 + '_stock'], axis=1, inplace=True)
    # Drop rows with all zeros
    df_total = df_combined[(df_combined.T != 0).any()]
    # Getting rid of useless columns here
    df_total.drop(['name', 'system', 'stock_count'], axis=1, inplace=True)
    # Remove rows without a need for items
    df_total = df_total.clip_lower(0)
    # Place ships in index to remove any all zero values
    df_total_grouped = df_total.groupby(['fit']).sum()
    df_clean = df_total_grouped[(df_total_grouped.T !=0).any()]
    # Convert back to original dict format
    clean_dict = df_clean.to_dict()

    return clean_dict

def merge_df(df_grouped, df_stock):
    df_merged = df_grouped.merge(df_stock, left_on=['system', 'item_name'], right_on=['system', 'name'], how='left')
    df_merged.fillna(0, inplace=True)
    df_merged['quantity'] = df_merged['quantity'].astype(int)
    df_merged['item_count'] = df_merged['item_count'] - df_merged['quantity']
    df_result = df_merged[df_merged['item_count'] > 0][['system', 'item_type', 'item_name', 'item_count']]

    return df_result

def main():
    fit_list = load_fits()
    df_assembled, df_stock = stock()
    clean_dict = current_needs(df_assembled)
    df = fits_dataframe(fit_list, clean_dict)
    df_grouped = df.groupby(['system', 'item_type', 'item_name'], as_index=False).sum()
    
    df_grouped = df_grouped[['system', 'item_type', 'item_name', 'item_count']].sort_values(['system', 'item_type', 'item_name', 'item_count'], ascending=[True, False, True, False])
    
    df_merged = merge_df(df_grouped, df_stock)
    
    writer = pd.ExcelWriter('fit_summary.xlsx', engine='xlsxwriter')
    df_merged.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    
    print "Complete!!!"
