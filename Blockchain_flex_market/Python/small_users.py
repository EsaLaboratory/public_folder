import copy
import random
import time

from web3 import Web3
from time import sleep
from random import gauss, uniform

import main_contract_spec as main_contract_spec
import aggregator_contract_spec as agg_contract_spec

USERS = 50

w3 = Web3(provider=Web3.HTTPProvider('http://127.0.0.1:8545', request_kwargs={'timeout': 60*10}))
assert (w3.isConnected())

main_contract = w3.eth.contract(address=main_contract_spec.MAIN_CONTRACT_ADDRESS, abi=main_contract_spec.abi)

filter_open_market = main_contract.events.open_market.createFilter(fromBlock="latest")
filter_accepted_bids_submitted = main_contract.events.accepted_bids_submitted.createFilter(fromBlock="latest")

print("Market close, waiting..")

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
            account = w3.eth.account.from_key(random.randbytes(32))

            my_accounts[account.address] = [account, address, agg_contract]

            if bid_type == 'up':
                price_penny_per_kWh = int(uniform(1, 7.5))  # p/kWh
                quantity_kW = int(uniform(1, 3))  # 2kW mean
            else:  # 'down'
                price_penny_per_kWh = int(uniform(1, 7.5))  # p/kWh
                quantity_kW = int(uniform(1, 3))  # 2kW mean

            # we ensure that there is at least one order at the start and one at the end of the sett_p
            if i % 2 == 1:
                t1 = 0
                t2 = int(random.uniform(1, 30))
            elif i % 2 == 0:
                t1 = int(random.uniform(0, 29))
                t2 = 29

            # print(t1, t2)
            assert t1 < t2
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

print('Waiting for payments.. ')
while accepted_bid_profiles:
    for filter_paid in filter_log_paid:
        for log in filter_paid.get_new_entries():
            e = log['args']

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

