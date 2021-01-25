import json
import requests
import datetime

import numpy as np
import pandas as pd
import math as m

from web3 import Web3
from statistics import mean
from sklearn.model_selection import train_test_split
from operator import methodcaller

max_blocks_count = 99999999

print('Are we going to write/rewrite down the main data? (Yes/No)')
write_down_main_data = True if input().lower() == 'yes' else False

print('How many neighbours shall we count?')
neighbours = int(input())

print('Train/Test parts coefficient?')
test_train_coef = float(input())

print('Use sample or whole? (yes = sample, no = other)')
use_sample = True if input().lower() == 'yes' else False

sample_size = 0
using_clusters = []
count_clusters = 0
use_specific = False

if use_sample:
    print('Specify the sample size.')
    sample_size = int(input())
else:
    print('Use specific clusters or whole? (yes = specific, no = whole)')
    use_specific = True if input().lower() == 'yes' else False
    if use_specific:
        print('Specify count of clusters please:')
        count_clusters = int(input())
        for i in range(count_clusters):
            print('Now specify {} cluster'.format(i))
            using_clusters.append(int(input()))

if write_down_main_data:
    print('Rewriting main data...')
else:
    print('Using already loaded main_data...')

def all_transactions_of_address(address, blocks_count, key):
    url = 'http://api.etherscan.io/api?module=account&action=txlist&address={}&startblock=0&endblock={}&sort=asc&apikey={}'.format(str(address), str(blocks_count), str(key))
    response = requests.get(url).json()
    result = []
    if response['message'] == 'OK':
        for transaction in response['result']:
            result.append(transaction)
    else:
        print('Tried address {} - Status code: {}, Message: {}'.format(address, response['status'], response['message']))
    return result

def from_wei(wei):
    return float(Web3.fromWei(int(wei), 'ether'))

def activation_func(x):
    return 1 / x * x if x != 0 else m.inf

def bedrin_metric(scammer, address, blocks_count, key):
    k_neg, k_pos, neg_mean_value, pos_mean_value = extract_parameters(scammer, address, blocks_count, key)
    return activation_func((k_pos * pos_mean_value) - (k_neg * neg_mean_value))

def extract_parameters(scammer, address, blocks_count, key):
    transactions = all_transactions_of_address(scammer, blocks_count, key)
    k_neg = len([t for t in transactions if t['from'] == scammer and t['to'] == address])
    k_pos = len([t for t in transactions if t['from'] == address and t['to'] == scammer])
    neg_mean_value = 0
    pos_mean_value = 0
    if k_neg > 0:
        neg_mean_value = mean([from_wei(t['value']) for t in transactions if t['from'] == scammer and t['to'] == address])
    if k_pos > 0:
        pos_mean_value = mean([from_wei(t['value']) for t in transactions if t['from'] == address and t['to'] == scammer])
    return k_neg, k_pos, neg_mean_value, pos_mean_value

with open('./api_key.json', mode='r') as key_file:
    key = json.loads(key_file.read())['key']

with open('./scam_data.json', mode='r') as scam_data_file:
    scam_data = json.loads(scam_data_file.read())

scam_addresses = []
for s in filter(Web3.isAddress, scam_data['result'].keys()):
    scam_addresses.append(s)

main_data = pd.DataFrame(columns=['address', 'cluster'])
filename = 'main_data.csv'

if write_down_main_data:
    for idx, scam_addr in enumerate(scam_addresses):
        transactions = all_transactions_of_address(scam_addr, max_blocks_count, key)
        if len(transactions) > 0:
            main_data = main_data.append({'address': scam_addr, 'cluster': idx}, ignore_index=True)
        all_relative_addresses = set()
        for transaction in transactions:
            all_relative_addresses.add(transaction['from'])
            all_relative_addresses.add(transaction['to'])
        for address in all_relative_addresses:
            main_data = main_data.append({'address': address, 'cluster': idx}, ignore_index=True)
    main_data.to_csv(filename)
else:
    main_data = pd.read_csv(filename, index_col=0)

print('Using main data\n', main_data)

formatted_main_data = []
if use_sample:
    formatted_main_data = main_data.sample(n=sample_size)
else:
    if use_specific:
        formatted_main_data = main_data[main_data['cluster'].isin(using_clusters)]
    else:
        formatted_main_data = main_data.copy()

print('Splittings data...')
train, test = train_test_split(formatted_main_data, test_size=test_train_coef)

print('Train data\n', train)
print('Test data\n', test)

temporal_data = train.copy()
temporal_data['is_old'] = True

def sort_by_metric(address, blocks_count, key):
    def new_key(row):
        result_metric = bedrin_metric(row[1]['address'], address, blocks_count, key)
        print('Metric of {} is {}'.format(row[1]['address'], result_metric))
        return result_metric
    return new_key

# print(bedrin_metric('0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0', '0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0', max_blocks_count, key))

for test_idx, test_row in test.iterrows():
    print('--Begin--')
    print('test_idx = {}, test_row = {}'.format(test_idx, test_row['address']))
    nearest_neighbours = sorted(train.iterrows(), key=sort_by_metric(test_row['address'], max_blocks_count, key))[:neighbours]
    print('Found nearest_neighbours = {}'.format(nearest_neighbours))
    clusters_of_neighbours = []
    for neighbour in nearest_neighbours:
        clusters_of_neighbours.append(neighbour[1]['cluster'])
    print('Clusters are: {}'.format(clusters_of_neighbours))
    result_cluster = max(clusters_of_neighbours, key=clusters_of_neighbours.count)
    print('Result cluster: {}'.format(result_cluster))
    temporal_data = temporal_data.append({'address': test_row['address'], 'cluster': result_cluster, 'is_old': False}, ignore_index=True)
    print('Added address {} with cluster {}'.format(test_row['address'], result_cluster))
    print('--End--')

print('Temporal data\n', temporal_data)
