import copy
import random
import time

from web3 import Web3
from time import sleep
from random import gauss, uniform

import main_contract_spec as main_contract_spec
import aggregator_contract_spec as agg_contract_spec

USERS = 3

w3 = Web3(provider=Web3.HTTPProvider('http://127.0.0.1:8545', request_kwargs={'timeout': 60*10}))
assert (w3.isConnected())

main_contract = w3.eth.contract(address=main_contract_spec.MAIN_CONTRACT_ADDRESS, abi=main_contract_spec.abi)

filter_open_market = main_contract.events.open_market.createFilter(fromBlock="latest")
filter_accepted_bids_submitted = main_contract.events.accepted_bids_submitted.createFilter(fromBlock="latest")

print("TEST4.3: accepted bid UP must be 10kW instead that 11kW")

while True:
    if e := filter_open_market.get_new_entries():
        data = e[0].args
        break
    sleep(2)

t = time.time()
print("Market open. Child contracts:")
print(f'node: {data.node1} address:{data.deployed_agg_node1_address}')
print(f'node: {data.node2} address:{data.deployed_agg_node2_address}')
print(f'node: {data.node3} address:{data.deployed_agg_node3_address}')

ch_smart_c = {}
ch_smart_c[data.node1] = [data.deployed_agg_node1_address, w3.eth.contract(address=data.deployed_agg_node1_address, abi=agg_contract_spec.abi)]
ch_smart_c[data.node2] = [data.deployed_agg_node2_address, w3.eth.contract(address=data.deployed_agg_node2_address, abi=agg_contract_spec.abi)]
ch_smart_c[data.node3] = [data.deployed_agg_node3_address, w3.eth.contract(address=data.deployed_agg_node3_address, abi=agg_contract_spec.abi)]

filter_log_accepted_profile = []
filter_log_paid = []
for c in ch_smart_c.values():
    child_contract = c[1]
    filter_log_accepted_profile.append(child_contract.events.log_accepted_profile.createFilter(fromBlock="latest"))
    filter_log_paid.append(child_contract.events.pay_small_user.createFilter(fromBlock="latest"))


previous_block = w3.eth.get_block_number()
bids = {}
my_accounts = {}
random.seed(1337)
ref = 0
for (node, [address, agg_contract]) in ch_smart_c.items():

    print(f'Sending bids to child contract {node}: {address}')

    for bid_type in ['up', 'down']:
        for i in range(1, USERS+1):

            if not ((bid_type == 'up' and node == 'a') or (bid_type == 'down' and node == 'b')):
                continue

            account = w3.eth.account.from_key(random.randbytes(32))

            my_accounts[account.address] = [account, address, agg_contract]

            if i == 1:
                t1 = 0
                t2 = 26
                quantity_kW = 5
                price_penny_per_kWh = 10
            elif i == 2:
                t1 = 0
                t2 = 20
                quantity_kW = 6
                price_penny_per_kWh = 15
            elif i == 3:
                t1 = 15
                t2 = 29
                quantity_kW = 12
                price_penny_per_kWh = 20

            # print(t1, t2)

            assert t1 >= 0
            assert t2 <= 29

            transaction = {
                        'to': address,
                        'value': w3.toWei(0, 'ether'),
                        'gasPrice': 0,
                        'nonce': w3.eth.get_transaction_count(account.address),
                        'chainId': w3.eth.chain_id,
                        'data': agg_contract.encodeABI(fn_name="aggregator_submit_bid",
                                                       args=[ref, data.sett_p, node, bid_type, price_penny_per_kWh, quantity_kW, t1, t2])
            }
            transaction['gas'] = 2100000000

            signed_tx = account.sign_transaction(transaction)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            assert(tx_receipt.status)

            bids[account.address + str(ref)] = [data.sett_p, node, bid_type, price_penny_per_kWh, quantity_kW]

            ref += 1

print('done')

print('Waiting for small users\' accepted bid profiles..')
accepted_bid_profiles = []
while True:
    for filter_acc_profiles in filter_log_accepted_profile:
        for log in filter_acc_profiles.get_new_entries():
            e = log['args']

            if e.sender + str(e.ref) in bids:
                accepted_bid_profiles.append(e)

                print(f'bid_id:{"%2d" % e.bid_id} ref:{"%d" % e.ref} '
                      f'sett_p:{"%2d" % e.sett_p} sender:{e.sender} '
                      f'node:{e.node} bid_type:{e.bid_type} price_penny_per_kWh:{e.price_penny_per_kWh} '
                      f't0:{e.t0} t1:{e.t1} t2:{e.t2} t3:{e.t3} t4:{e.t4} t5:{e.t5} t6:{e.t6} t7:{e.t7} t8:{e.t8} '
                      f't9:{e.t9} t10:{e.t10} t11:{e.t11} t12:{e.t12} t13:{e.t13} t14:{e.t14} t15:{e.t15} t16:{e.t16} '
                      f't17:{e.t17} t18:{e.t18} t19:{e.t19} t20:{e.t20} t21:{e.t21} t22:{e.t22} t23:{e.t23} t24:{e.t24} '
                      f't25:{e.t25} t26:{e.t26} t27:{e.t27} t28:{e.t28} t29:{e.t29}')

    if filter_accepted_bids_submitted.get_new_entries():
        print('All accepted bid profiles submitted')
        break
    sleep(2)

print('Sending metered data..', end='')
for e in copy.deepcopy(accepted_bid_profiles):

    account = my_accounts[e.sender][0]
    agg_address = my_accounts[e.sender][1]
    agg_contract = my_accounts[e.sender][2]

    e_list = [e.t0, e.t1, e.t2, e.t3, e.t4, e.t5, e.t6, e.t7, e.t8,
              e.t9, e.t10, e.t11, e.t12, e.t13, e.t14, e.t15, e.t16,
              e.t17, e.t18, e.t19, e.t20, e.t21, e.t22, e.t23, e.t24,
              e.t25, e.t26, e.t27, e.t28, e.t29]

    if sum(e_list) == 0:  # order is not accepted
        accepted_bid_profiles.remove(e)
        continue

    if e.ref == 1:
        for i in range(0, 30):
            if e_list[i] != 0:
                e_list[i] = 4

    if e.ref == 2:
        for i in range(21, 30):
            e_list[i] = 3
            if i >= 27:
                e_list[i] = 7

    # e_list[0] = 0
    e_list = [int(x) for x in e_list]

    transaction = {
                'to': agg_address,
                'value': w3.toWei(0, 'ether'),
                'gasPrice': 0,
                'nonce': w3.eth.get_transaction_count(account.address),
                'chainId': w3.eth.chain_id,
                'data': agg_contract.encodeABI(fn_name="agg_submit_metered_data",
                                                args=[e.bid_id, e.ref, e.sett_p, e.sender, e.node,
                                                      e.bid_type, e.price_penny_per_kWh, e_list])
    }
    transaction['gas'] = 2100000000  # using estimate_gas gives problem with assert sender == msg.sender

    signed_tx = account.sign_transaction(transaction)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    assert(tx_receipt.status)

print('done')

out = {}

print('Waiting for payments.. ')
while accepted_bid_profiles:
    for filter_paid in filter_log_paid:
        for log in filter_paid.get_new_entries():
            e = log['args']

            out[e] = e

            for data in accepted_bid_profiles:
                if e.sender == data.sender and e.ref == data.ref:
                    accepted_bid_profiles.remove(data)
                    break

            previous_balance = w3.eth.get_balance(e.sender, block_identifier=previous_block)
            new_balance = w3.eth.get_balance(e.sender)
            print(f'PAID: sender:{e.sender} ref:{e.ref} price_penny_per_kWh:{e.price_penny_per_kWh} to_pay_in_hundredths_of_a_penny:{e.to_pay_in_hundredths_of_a_penny}')
            print(f'previuos balance (WEI):{previous_balance} new balance (WEI):{new_balance}')
            assert new_balance - previous_balance == e.to_pay_in_hundredths_of_a_penny

    sleep(2)

print(f"All paid. Time elapsed since start {'%.0f' % (time.time() - t)} seconds.")

from decimal import Decimal
from web3.datastructures import AttributeDict

print(out)

if out == {AttributeDict({'bid_id': 0, 'ref': 0, 'sender': '0xAA2dEb8Eb11f76F91DF802e83205B00c99Cac181', 'price_penny_per_kWh': 10, 'metered_indiv_power': 135, 'metered_pay': 22500000, 'penality': Decimal('30.1'), 'imbalance': 0, 'imbalance_tot': 42, 'imbalance_share': Decimal('0'), 'individual_penality': 0, 'to_pay_in_hundredths_of_a_penny': 2250}): AttributeDict({'bid_id': 0, 'ref': 0, 'sender': '0xAA2dEb8Eb11f76F91DF802e83205B00c99Cac181', 'price_penny_per_kWh': 10, 'metered_indiv_power': 135, 'metered_pay': 22500000, 'penality': Decimal('30.1'), 'imbalance': 0, 'imbalance_tot': 42, 'imbalance_share': Decimal('0'), 'individual_penality': 0, 'to_pay_in_hundredths_of_a_penny': 2250}), AttributeDict({'bid_id': 1, 'ref': 1, 'sender': '0x9cB517992bb2C111b83eEABd91d995D6dd6435D5', 'price_penny_per_kWh': 15, 'metered_indiv_power': 84, 'metered_pay': 21000000, 'penality': Decimal('30.1'), 'imbalance': 21, 'imbalance_tot': 42, 'imbalance_share': Decimal('0.5'), 'individual_penality': 15050000, 'to_pay_in_hundredths_of_a_penny': 595}): AttributeDict({'bid_id': 1, 'ref': 1, 'sender': '0x9cB517992bb2C111b83eEABd91d995D6dd6435D5', 'price_penny_per_kWh': 15, 'metered_indiv_power': 84, 'metered_pay': 21000000, 'penality': Decimal('30.1'), 'imbalance': 21, 'imbalance_tot': 42, 'imbalance_share': Decimal('0.5'), 'individual_penality': 15050000, 'to_pay_in_hundredths_of_a_penny': 595}), AttributeDict({'bid_id': 2, 'ref': 2, 'sender': '0xF07eAC74778f1D7B0382D97Fac0D6126EED94EEE', 'price_penny_per_kWh': 20, 'metered_indiv_power': 39, 'metered_pay': 13000000, 'penality': Decimal('30.1'), 'imbalance': 21, 'imbalance_tot': 42, 'imbalance_share': Decimal('0.5'), 'individual_penality': 15050000, 'to_pay_in_hundredths_of_a_penny': 0}): AttributeDict({'bid_id': 2, 'ref': 2, 'sender': '0xF07eAC74778f1D7B0382D97Fac0D6126EED94EEE', 'price_penny_per_kWh': 20, 'metered_indiv_power': 39, 'metered_pay': 13000000, 'penality': Decimal('30.1'), 'imbalance': 21, 'imbalance_tot': 42, 'imbalance_share': Decimal('0.5'), 'individual_penality': 15050000, 'to_pay_in_hundredths_of_a_penny': 0}), AttributeDict({'bid_id': 0, 'ref': 3, 'sender': '0x7684e31030964f5AF95CD7b130f8f81fAfe2A6DE', 'price_penny_per_kWh': 10, 'metered_indiv_power': 135, 'metered_pay': 22500000, 'penality': Decimal('0'), 'imbalance': 0, 'imbalance_tot': 0, 'imbalance_share': Decimal('0'), 'individual_penality': 0, 'to_pay_in_hundredths_of_a_penny': 2250}): AttributeDict({'bid_id': 0, 'ref': 3, 'sender': '0x7684e31030964f5AF95CD7b130f8f81fAfe2A6DE', 'price_penny_per_kWh': 10, 'metered_indiv_power': 135, 'metered_pay': 22500000, 'penality': Decimal('0'), 'imbalance': 0, 'imbalance_tot': 0, 'imbalance_share': Decimal('0'), 'individual_penality': 0, 'to_pay_in_hundredths_of_a_penny': 2250}), AttributeDict({'bid_id': 1, 'ref': 4, 'sender': '0x36E379b770E83b0CDD94CfDCBA063f753EFD6b8d', 'price_penny_per_kWh': 15, 'metered_indiv_power': 126, 'metered_pay': 31500000, 'penality': Decimal('0'), 'imbalance': 0, 'imbalance_tot': 0, 'imbalance_share': Decimal('0'), 'individual_penality': 0, 'to_pay_in_hundredths_of_a_penny': 3150}): AttributeDict({'bid_id': 1, 'ref': 4, 'sender': '0x36E379b770E83b0CDD94CfDCBA063f753EFD6b8d', 'price_penny_per_kWh': 15, 'metered_indiv_power': 126, 'metered_pay': 31500000, 'penality': Decimal('0'), 'imbalance': 0, 'imbalance_tot': 0, 'imbalance_share': Decimal('0'), 'individual_penality': 0, 'to_pay_in_hundredths_of_a_penny': 3150}), AttributeDict({'bid_id': 2, 'ref': 5, 'sender': '0x22668894cDa468B4cfC7FD836190A6D9Cea3c589', 'price_penny_per_kWh': 20, 'metered_indiv_power': 69, 'metered_pay': 23000000, 'penality': Decimal('0'), 'imbalance': 0, 'imbalance_tot': 0, 'imbalance_share': Decimal('0'), 'individual_penality': 0, 'to_pay_in_hundredths_of_a_penny': 2300}): AttributeDict({'bid_id': 2, 'ref': 5, 'sender': '0x22668894cDa468B4cfC7FD836190A6D9Cea3c589', 'price_penny_per_kWh': 20, 'metered_indiv_power': 69, 'metered_pay': 23000000, 'penality': Decimal('0'), 'imbalance': 0, 'imbalance_tot': 0, 'imbalance_share': Decimal('0'), 'individual_penality': 0, 'to_pay_in_hundredths_of_a_penny': 2300})}:
    print("Test PASSED")
else:
    raise Exception

