from web3 import Web3
from time import sleep
import pandas as pd

from main_contract_spec import *

w3 = Web3(provider=Web3.HTTPProvider('http://127.0.0.1:8545', request_kwargs={'timeout': 60*10}))
assert (w3.isConnected())

main_contract = w3.eth.contract(address=MAIN_CONTRACT_ADDRESS, abi=abi)

filter_open_market = main_contract.events.open_market.createFilter(fromBlock="latest")
filter_received_bid = main_contract.events.received_bid.createFilter(fromBlock="latest")
filter_gate_closure = main_contract.events.gate_closure.createFilter(fromBlock="latest")
filter_accepted_bid = main_contract.events.accepted_bid.createFilter(fromBlock="latest")
filter_accepted_bids_submitted = main_contract.events.accepted_bids_submitted.createFilter(fromBlock="latest")
filter_paid_agg = main_contract.events.paid_agg.createFilter(fromBlock="latest")
filter_paid = main_contract.events.paid.createFilter(fromBlock="latest")
filter_payment_received = main_contract.events.payment_received.createFilter(fromBlock="latest")



print("Market close, waiting..")

while True:
    if filter_open_market.get_new_entries():
        print('Market open: waiting for bids')
        break
    sleep(2)

bids = []
while True:

    for log in filter_received_bid.get_new_entries():
        e = log['args']

        bids.append([e.bid_id, e.ref, e.sett_p, e.sender, e.node, e.bid_type, e.price_penny_per_kWh, e.quantity_kW])

        print(f'bid_id:{"%2d" % e.bid_id} ref:{"%d" % e.ref} '
              f'sett_p:{"%2d" % e.sett_p} sender:{e.sender} '
              f'node:{e.node} bid_type:{e.bid_type} price_penny_per_kWh:{e.price_penny_per_kWh} quantity_kW:{e.quantity_kW}')

    if filter_gate_closure.get_all_entries():
        print('Market close')
        break

    sleep(2)

pd.DataFrame(bids, columns=['bid_id', 'ref', 'sett_p', 'sender', 'node', 'bid_type', 'price_penny_per_kWh',
                            'quantity_kW']).to_excel('collected_bids.xlsx', index=None)

# this is the file that can be edited
# pd.DataFrame(bids, columns=['bid_id', 'ref', 'sett_p', 'sender', 'node', 'bid_type', 'price_penny_per_kWh',
#                             'quantity_kW']).to_excel('accepted_bids.xlsx', index=None)

print('Logging accepted bids..')
accepted_bids = {}
while True:
    for log in filter_accepted_bid.get_new_entries():
        e = log['args']

        accepted_bids[e.bid_id] = dict(e)

        print(f'bid_id:{"%2d" % e.bid_id} ref:{"%d" % e.ref} '
              f'sett_p:{"%2d" % e.sett_p} sender:{e.sender} '
              f'node:{e.node} bid_type:{e.bid_type} price_penny_per_kWh:{e.price_penny_per_kWh} quantity_kW:{e.quantity_kW}')

    if filter_accepted_bids_submitted.get_new_entries():
        print('All accepted bids submitted')
        break

    sleep(2)

print('Logging payments..')
while True:
    for log in filter_paid.get_new_entries():
        e = log['args']
        print(f'PAID: sender:{e.sender} ref:{e.ref} price_penny_per_kWh:{e.price_penny_per_kWh} metered_quantity_kW:{e.metered_quantity_kW} '
              f'expected_quantity_kW:{e.expected_quantity_kW} '
              f'to_pay_in_hundredths_of_a_penny:{e.to_pay_in_hundredths_of_a_penny}')

    for log in filter_paid_agg.get_new_entries():
        e = log['args']
        print(f'PAID_AGG: sender:{e.sender} ref:{e.ref} price_penny_per_kWh:{e.price_penny_per_kWh} metered_quantity_kW:{e.metered_quantity_kW} '
              f'expected_quantity_kW:{e.expected_quantity_kW} '
              f'to_pay_in_hundredths_of_a_penny:{e.to_pay_in_hundredths_of_a_penny}')

    for log in filter_payment_received.get_new_entries():
        e = log['args']
        print(f'Self-destruct: sender:{e.sender} received value:{e.value}')

    sleep(2)

