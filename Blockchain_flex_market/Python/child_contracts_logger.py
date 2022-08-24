from web3 import Web3
from time import sleep
from pprint import pprint

import main_contract_spec as main_contract_spec
import aggregator_contract_spec as agg_contract_spec

w3 = Web3(provider=Web3.HTTPProvider('http://127.0.0.1:8545', request_kwargs={'timeout': 60*10}))
assert (w3.isConnected())

main_contract = w3.eth.contract(address=main_contract_spec.MAIN_CONTRACT_ADDRESS, abi=main_contract_spec.abi)

filter_open_market = main_contract.events.open_market.createFilter(fromBlock="latest")

print("Market close, waiting..")

while True:
    if e := filter_open_market.get_new_entries():
        data = e[0].args
        break
    sleep(2)

print("Market open. Child contracts:")
print(f'node: {data.node1} address:{data.deployed_agg_node1_address}')
print(f'node: {data.node2} address:{data.deployed_agg_node2_address}')
print(f'node: {data.node3} address:{data.deployed_agg_node3_address}')

agg_contract_node1 = w3.eth.contract(address=data.deployed_agg_node1_address, abi=agg_contract_spec.abi)
agg_contract_node2 = w3.eth.contract(address=data.deployed_agg_node2_address, abi=agg_contract_spec.abi)
agg_contract_node3 = w3.eth.contract(address=data.deployed_agg_node3_address, abi=agg_contract_spec.abi)

filter_received_bid_node1 = agg_contract_node1.events.received_bid.createFilter(fromBlock="latest")
filter_received_bid_node2 = agg_contract_node2.events.received_bid.createFilter(fromBlock="latest")
filter_received_bid_node3 = agg_contract_node3.events.received_bid.createFilter(fromBlock="latest")

filter_log_profile_node1 = agg_contract_node1.events.log_profile.createFilter(fromBlock="latest")
filter_log_profile_node2 = agg_contract_node2.events.log_profile.createFilter(fromBlock="latest")
filter_log_profile_node3 = agg_contract_node3.events.log_profile.createFilter(fromBlock="latest")

filter_my_send_agg_meter_node1 = agg_contract_node1.events.send_agg_meter.createFilter(fromBlock="latest")
filter_my_send_agg_meter_node2 = agg_contract_node2.events.send_agg_meter.createFilter(fromBlock="latest")
filter_my_send_agg_meter_node3 = agg_contract_node3.events.send_agg_meter.createFilter(fromBlock="latest")

filter_payment_received_node1 = agg_contract_node1.events.payment_received.createFilter(fromBlock="latest")
filter_payment_received_node2 = agg_contract_node2.events.payment_received.createFilter(fromBlock="latest")
filter_payment_received_node3 = agg_contract_node3.events.payment_received.createFilter(fromBlock="latest")

filter_pay_small_user_node1 = agg_contract_node1.events.pay_small_user.createFilter(fromBlock="latest")
filter_pay_small_user_node2 = agg_contract_node2.events.pay_small_user.createFilter(fromBlock="latest")
filter_pay_small_user_node3 = agg_contract_node3.events.pay_small_user.createFilter(fromBlock="latest")

filter_log_received_metered_node1 = agg_contract_node1.events.log_received_metered.createFilter(fromBlock="latest")
filter_log_received_metered_node2 = agg_contract_node2.events.log_received_metered.createFilter(fromBlock="latest")
filter_log_received_metered_node3 = agg_contract_node3.events.log_received_metered.createFilter(fromBlock="latest")


while True:
    for log in filter_received_bid_node1.get_new_entries():
        e = log['args']

        print(f'bid_id:{"%2d" % e.bid_id} ref:{"%d" % e.ref} '
              f'sett_p:{"%2d" % e.sett_p} sender:{e.sender} '
              f'node:{e.node} bid_type:{e.bid_type} price_penny_per_kWh:{e.price_penny_per_kWh} quantity_kW:{e.quantity_kW} '
              f't1:{e.t1} t2:{e.t2}')

    for log in filter_received_bid_node2.get_new_entries():
        e = log['args']

        print(f'bid_id:{"%2d" % e.bid_id} ref:{"%d" % e.ref} '
              f'sett_p:{"%2d" % e.sett_p} sender:{e.sender} '
              f'node:{e.node} bid_type:{e.bid_type} price_penny_per_kWh:{e.price_penny_per_kWh} quantity_kW:{e.quantity_kW} '
              f't1:{e.t1} t2:{e.t2}')

    for log in filter_received_bid_node3.get_new_entries():
        e = log['args']

        print(f'bid_id:{"%2d" % e.bid_id} ref:{"%d" % e.ref} '
              f'sett_p:{"%2d" % e.sett_p} sender:{e.sender} '
              f'node:{e.node} bid_type:{e.bid_type} price_penny_per_kWh:{e.price_penny_per_kWh} quantity_kW:{e.quantity_kW} '
              f't1:{e.t1} t2:{e.t2}')

    for log in filter_log_profile_node1.get_new_entries():
        e = log['args']
        print(f'bid_id:{"%2d" % e.bid_id} ref:{"%d" % e.ref} '
              f'sett_p:{"%2d" % e.sett_p} sender:{e.sender} '
              f'node:{e.node} bid_type:{e.bid_type} price_penny_per_kWh:{e.price_penny_per_kWh} '
              f't0:{e.t0} t1:{e.t1} t2:{e.t2} t3:{e.t3} t4:{e.t4} t5:{e.t5} t6:{e.t6} t7:{e.t7} t8:{e.t8} '
              f't9:{e.t9} t10:{e.t10} t11:{e.t11} t12:{e.t12} t13:{e.t13} t14:{e.t14} t15:{e.t15} t16:{e.t16} '
              f't17:{e.t17} t18:{e.t18} t19:{e.t19} t20:{e.t20} t21:{e.t21} t22:{e.t22} t23:{e.t23} t24:{e.t24} '
              f't25:{e.t25} t26:{e.t26} t27:{e.t27} t28:{e.t28} t29:{e.t29}')

    for log in filter_log_profile_node2.get_new_entries():
        e = log['args']
        print(f'bid_id:{"%2d" % e.bid_id} ref:{"%d" % e.ref} '
              f'sett_p:{"%2d" % e.sett_p} sender:{e.sender} '
              f'node:{e.node} bid_type:{e.bid_type} price_penny_per_kWh:{e.price_penny_per_kWh} '
              f't0:{e.t0} t1:{e.t1} t2:{e.t2} t3:{e.t3} t4:{e.t4} t5:{e.t5} t6:{e.t6} t7:{e.t7} t8:{e.t8} '
              f't9:{e.t9} t10:{e.t10} t11:{e.t11} t12:{e.t12} t13:{e.t13} t14:{e.t14} t15:{e.t15} t16:{e.t16} '
              f't17:{e.t17} t18:{e.t18} t19:{e.t19} t20:{e.t20} t21:{e.t21} t22:{e.t22} t23:{e.t23} t24:{e.t24} '
              f't25:{e.t25} t26:{e.t26} t27:{e.t27} t28:{e.t28} t29:{e.t29}')

    for log in filter_log_profile_node3.get_new_entries():
        e = log['args']
        print(f'bid_id:{"%2d" % e.bid_id} ref:{"%d" % e.ref} '
              f'sett_p:{"%2d" % e.sett_p} sender:{e.sender} '
              f'node:{e.node} bid_type:{e.bid_type} price_penny_per_kWh:{e.price_penny_per_kWh} '
              f't0:{e.t0} t1:{e.t1} t2:{e.t2} t3:{e.t3} t4:{e.t4} t5:{e.t5} t6:{e.t6} t7:{e.t7} t8:{e.t8} '
              f't9:{e.t9} t10:{e.t10} t11:{e.t11} t12:{e.t12} t13:{e.t13} t14:{e.t14} t15:{e.t15} t16:{e.t16} '
              f't17:{e.t17} t18:{e.t18} t19:{e.t19} t20:{e.t20} t21:{e.t21} t22:{e.t22} t23:{e.t23} t24:{e.t24} '
              f't25:{e.t25} t26:{e.t26} t27:{e.t27} t28:{e.t28} t29:{e.t29}')

    for log in filter_log_received_metered_node1.get_new_entries():
        e = log['args']
        print(f'METERED: bid_id:{"%2d" % e.bid_id} ref:{"%d" % e.ref} '
              f'sett_p:{"%2d" % e.sett_p} '
              f'node:{e.node} bid_type:{e.bid_type} price_penny_per_kWh:{e.price_penny_per_kWh} '
              f't0:{e.metered[0]} t1:{e.metered[1]} t2:{e.metered[2]} t3:{e.metered[3]} t4:{e.metered[4]} t5:{e.metered[5]} t6:{e.metered[6]} t7:{e.metered[7]} t8:{e.metered[8]} '
              f't9:{e.metered[9]} t10:{e.metered[10]} t11:{e.metered[11]} t12:{e.metered[12]} t13:{e.metered[13]} t14:{e.metered[14]} t15:{e.metered[15]} t16:{e.metered[16]} '
              f't17:{e.metered[17]} t18:{e.metered[18]} t19:{e.metered[19]} t20:{e.metered[20]} t21:{e.metered[21]} t22:{e.metered[22]} t23:{e.metered[23]} t24:{e.metered[24]} '
              f't25:{e.metered[25]} t26:{e.metered[26]} t27:{e.metered[27]} t28:{e.metered[28]} t29:{e.metered[29]}')

    for log in filter_log_received_metered_node2.get_new_entries():
        e = log['args']
        print(f'METERED: bid_id:{"%2d" % e.bid_id} ref:{"%d" % e.ref} '
              f'sett_p:{"%2d" % e.sett_p} '
              f'node:{e.node} bid_type:{e.bid_type} price_penny_per_kWh:{e.price_penny_per_kWh} '
              f't0:{e.metered[0]} t1:{e.metered[1]} t2:{e.metered[2]} t3:{e.metered[3]} t4:{e.metered[4]} t5:{e.metered[5]} t6:{e.metered[6]} t7:{e.metered[7]} t8:{e.metered[8]} '
              f't9:{e.metered[9]} t10:{e.metered[10]} t11:{e.metered[11]} t12:{e.metered[12]} t13:{e.metered[13]} t14:{e.metered[14]} t15:{e.metered[15]} t16:{e.metered[16]} '
              f't17:{e.metered[17]} t18:{e.metered[18]} t19:{e.metered[19]} t20:{e.metered[20]} t21:{e.metered[21]} t22:{e.metered[22]} t23:{e.metered[23]} t24:{e.metered[24]} '
              f't25:{e.metered[25]} t26:{e.metered[26]} t27:{e.metered[27]} t28:{e.metered[28]} t29:{e.metered[29]}')

    for log in filter_log_received_metered_node3.get_new_entries():
        e = log['args']
        print(f'METERED: bid_id:{"%2d" % e.bid_id} ref:{"%d" % e.ref} '
              f'sett_p:{"%2d" % e.sett_p} '
              f'node:{e.node} bid_type:{e.bid_type} price_penny_per_kWh:{e.price_penny_per_kWh} '
              f't0:{e.metered[0]} t1:{e.metered[1]} t2:{e.metered[2]} t3:{e.metered[3]} t4:{e.metered[4]} t5:{e.metered[5]} t6:{e.metered[6]} t7:{e.metered[7]} t8:{e.metered[8]} '
              f't9:{e.metered[9]} t10:{e.metered[10]} t11:{e.metered[11]} t12:{e.metered[12]} t13:{e.metered[13]} t14:{e.metered[14]} t15:{e.metered[15]} t16:{e.metered[16]} '
              f't17:{e.metered[17]} t18:{e.metered[18]} t19:{e.metered[19]} t20:{e.metered[20]} t21:{e.metered[21]} t22:{e.metered[22]} t23:{e.metered[23]} t24:{e.metered[24]} '
              f't25:{e.metered[25]} t26:{e.metered[26]} t27:{e.metered[27]} t28:{e.metered[28]} t29:{e.metered[29]}')

    for log in filter_my_send_agg_meter_node1.get_new_entries():
        print('send_agg_meter_node1')
        e = log['args']
        pprint(e)

    for log in filter_my_send_agg_meter_node2.get_new_entries():
        print('send_agg_meter_node2')
        e = log['args']
        pprint(e)

    for log in filter_my_send_agg_meter_node3.get_new_entries():
        print('send_agg_meter_node3')
        e = log['args']
        pprint(e)

    for log in filter_payment_received_node1.get_new_entries():
        e = log['args']
        print('payment_received_node1')
        pprint(e)

    for log in filter_payment_received_node2.get_new_entries():
        print('payment_received_node2')
        e = log['args']
        pprint(e)

    for log in filter_payment_received_node3.get_new_entries():
        print('payment_received_node3')
        e = log['args']
        pprint(e)

    for log in filter_pay_small_user_node1.get_new_entries():
        e = log['args']
        print('pay_small_user_node1')
        pprint(e)

    for log in filter_pay_small_user_node2.get_new_entries():
        print('pay_small_user_node2')
        e = log['args']
        pprint(e)

    for log in filter_pay_small_user_node3.get_new_entries():
        print('pay_small_user_node3')
        e = log['args']
        pprint(e)

    sleep(3)





