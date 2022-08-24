import random
import time

from web3 import Web3
from time import sleep
from pprint import pprint
from random import gauss, uniform

from main_contract_spec import *

USERS = 2

w3 = Web3(provider=Web3.HTTPProvider('http://127.0.0.1:8545', request_kwargs={'timeout': 60*10}))
assert (w3.isConnected())

main_contract = w3.eth.contract(address=MAIN_CONTRACT_ADDRESS, abi=abi)

filter_open_market = main_contract.events.open_market.createFilter(fromBlock="latest")
filter_accepted_bid = main_contract.events.accepted_bid.createFilter(fromBlock="latest")
filter_accepted_bids_submitted = main_contract.events.accepted_bids_submitted.createFilter(fromBlock="latest")
filter_paid = main_contract.events.paid.createFilter(fromBlock="latest")

print("TEST LARGE USERS accepted kW ref 0 must be 50 kW instead of 56")

while True:
    if e := filter_open_market.get_new_entries():
        pprint(dict(e[0].args))
        order = e[0].args
        break
    sleep(2)

t = time.time()
print("Market open, sending bids.. ", end='')

previous_block = w3.eth.get_block_number()
bids = {}
my_accounts = {}
random.seed(12345)
ref = 0
for node in [order.node1, order.node2, order.node3]:
    for type in ['up', 'down']:
        for i in range(1, USERS+1):
            account = w3.eth.account.from_key(random.randbytes(32))

            my_accounts[account.address] = account

            if type == 'up':
                price_penny_per_kWh = max(int(gauss(50, 10)),0)
                quantity_kW = int(uniform(0, 100))
            else: # 'down'
                price_penny_per_kWh = max(int(gauss(50, 10)),0)
                quantity_kW = int(uniform(0, 100))

            transaction = {
                        'to': main_contract.address,
                        'value': w3.toWei(0, 'ether'),
                        'gasPrice': 0,
                        'nonce': w3.eth.get_transaction_count(account.address),
                        'chainId': w3.eth.chain_id,
                        'data': main_contract.encodeABI(fn_name="submit_bid", args=[ref,
                                                                                    order.sett_p, node,
                                                                                    type, price_penny_per_kWh, quantity_kW])
            }
            transaction['gas'] = 2100000000

            signed_tx = account.sign_transaction(transaction)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            assert(tx_receipt.status)

            bids[account.address + str(ref)] = [order.sett_p, node, type, price_penny_per_kWh, quantity_kW]

            ref += 1
    break
print('done')

print('Waiting for large users\' accepted bids..')
accepted_bids = []
while True:
    for log in filter_accepted_bid.get_new_entries():
        e = log['args']

        if e.sender + str(e.ref) in bids:
            accepted_bids.append(e)

            print(f'bid_id:{"%2d" % e.bid_id} ref:{"%d" % e.ref} '
                  f'sett_p:{"%2d" % e.sett_p} sender:{e.sender} '
                  f'node:{e.node} bid_type:{e.bid_type} price_penny_per_kWh:{e.price_penny_per_kWh} quantity_kW:{e.quantity_kW}')

    if filter_accepted_bids_submitted.get_new_entries():
        print('All accepted bids submitted')
        break

    sleep(2)

print('Sending metered data..', end='')
for e in accepted_bids:

    account = my_accounts[e.sender]

    metered_quantity_kW = e.quantity_kW
    if e.ref == 0:
        metered_quantity_kW *= 0.95
    elif e.ref == 1:
        metered_quantity_kW *= 0.75
    elif e.ref == 2:
        metered_quantity_kW *= 0.25

    transaction = {
                'to': main_contract.address,
                'value': w3.toWei(0, 'ether'),
                'gasPrice': 0,
                'nonce': w3.eth.get_transaction_count(account.address),
                'chainId': w3.eth.chain_id,
                'data': main_contract.encodeABI(fn_name="submit_metered_data_and_pay",
                                                args=[e.bid_id, e.ref, e.sett_p, e.sender, e.node,
                                                      e.bid_type, e.price_penny_per_kWh,
                                                      int(metered_quantity_kW)])
    }
    transaction['gas'] = 2100000000

    signed_tx = account.sign_transaction(transaction)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    assert(tx_receipt.status)

print('done')

out = {}

print('Waiting for payments.. ')
while accepted_bids:
    for log in filter_paid.get_new_entries():
        e = log['args']

        out[e] = e

        for data in accepted_bids:
            if e.sender == data.sender and e.ref == data.ref:
                accepted_bids.remove(data)
                break

        previous_balance = w3.eth.get_balance(e.sender, block_identifier=previous_block)
        new_balance = w3.eth.get_balance(e.sender)
        print(f'PAID: sender:{e.sender} ref:{e.ref} price_penny_per_kWh:{e.price_penny_per_kWh} metered_quantity_kW:{e.metered_quantity_kW} '
              f'expected_quantity_kW:{e.expected_quantity_kW} to_pay_in_hundredths_of_a_penny:{e.to_pay_in_hundredths_of_a_penny}')
        print(f'previuos balance (WEI):{previous_balance} '
              f'new balance (WEI):{new_balance}')
        assert new_balance - previous_balance == e.to_pay_in_hundredths_of_a_penny

    sleep(2)

print(f"All paid. Time elapsed since start {'%.0f' % (time.time() - t)} seconds.")

from decimal import Decimal
from web3.datastructures import AttributeDict

print(out)

if out == {AttributeDict({'sender': '0x11c09E31BeC9889b726731B52cBae159Dc36E1A1', 'ref': 0, 'price_penny_per_kWh': 45, 'metered_quantity_kW': 47, 'expected_quantity_kW': 50, 'to_pay_in_hundredths_of_a_penny': 105750}): AttributeDict({'sender': '0x11c09E31BeC9889b726731B52cBae159Dc36E1A1', 'ref': 0, 'price_penny_per_kWh': 45, 'metered_quantity_kW': 47, 'expected_quantity_kW': 50, 'to_pay_in_hundredths_of_a_penny': 105750}), AttributeDict({'sender': '0x218c18D7772304CA6D9800cb96CF85D4aF0396AC', 'ref': 1, 'price_penny_per_kWh': 54, 'metered_quantity_kW': 12, 'expected_quantity_kW': 17, 'to_pay_in_hundredths_of_a_penny': 16200}): AttributeDict({'sender': '0x218c18D7772304CA6D9800cb96CF85D4aF0396AC', 'ref': 1, 'price_penny_per_kWh': 54, 'metered_quantity_kW': 12, 'expected_quantity_kW': 17, 'to_pay_in_hundredths_of_a_penny': 16200}), AttributeDict({'sender': '0x31868FbFb7427cdD859C5C7998f9eDaEAD4E3776', 'ref': 2, 'price_penny_per_kWh': 60, 'metered_quantity_kW': 12, 'expected_quantity_kW': 50, 'to_pay_in_hundredths_of_a_penny': 0}): AttributeDict({'sender': '0x31868FbFb7427cdD859C5C7998f9eDaEAD4E3776', 'ref': 2, 'price_penny_per_kWh': 60, 'metered_quantity_kW': 12, 'expected_quantity_kW': 50, 'to_pay_in_hundredths_of_a_penny': 0}), AttributeDict({'sender': '0x11a09f2f09C8aCC0f453A9b777dFD869BdF4169a', 'ref': 3, 'price_penny_per_kWh': 48, 'metered_quantity_kW': 2, 'expected_quantity_kW': 2, 'to_pay_in_hundredths_of_a_penny': 4800}): AttributeDict({'sender': '0x11a09f2f09C8aCC0f453A9b777dFD869BdF4169a', 'ref': 3, 'price_penny_per_kWh': 48, 'metered_quantity_kW': 2, 'expected_quantity_kW': 2, 'to_pay_in_hundredths_of_a_penny': 4800})}:
    print("Test PASSED")
else:
    raise Exception