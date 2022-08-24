import os
from web3 import Web3
import pandas as pd
import time

w3 = Web3(provider=Web3.HTTPProvider('http://127.0.0.1:8545', request_kwargs={'timeout': 60*10}))
assert (w3.isConnected())

print("Compiling and deploying contracts..")

# compiling aggregator template
FILE = "aggregator_contract_spec.py"
with open(FILE, 'w') as f:
    print("false = False; true = True", file=f)
    print("abi = ", end='', file=f)

bashCommand = "vyper -f abi ../Vyper/aggregator_template.vy  >> " + FILE
os.system(bashCommand)

with open(FILE, 'a') as f:
    print("bytecode = ", end='', file=f)

bashCommand = "vyper -f bytecode ../Vyper/aggregator_template.vy  >> " + FILE
os.system(bashCommand)

# deploying aggregator template
import aggregator_contract_spec as AGG_CONTRACT
abstract_aggregator_contract = w3.eth.contract(abi=AGG_CONTRACT.abi, bytecode=AGG_CONTRACT.bytecode)
tx_hash = abstract_aggregator_contract.constructor().transact({'from': w3.eth.accounts[0], 'gas': 2100000000})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
assert(tx_receipt.status == 1)
print("* Aggregator template to create child smart contracts at", tx_receipt.contractAddress)

# removing old aggregator template address
FILE = "../Vyper/main_contract.vy"
with open(FILE, 'r') as f:
    lines = f.readlines()

with open(FILE, 'w') as f:
    for line in lines:
        if "AGGREGATOR_TEMPLATE_ADDRESS:" in line:
            line = "AGGREGATOR_TEMPLATE_ADDRESS: constant(address) = " + tx_receipt.contractAddress + "\n"
        f.writelines(line)

# compiling main contract
FILE = "main_contract_spec.py"
with open(FILE, 'w') as f:
    print("false = False; true = True", file=f)
    print("abi = ", end='', file=f)

bashCommand = "vyper -f abi ../Vyper/main_contract.vy  >> " + FILE
os.system(bashCommand)

with open(FILE, 'a') as f:
    print("bytecode = ", end='', file=f)

bashCommand = "vyper -f bytecode ../Vyper/main_contract.vy  >> " + FILE
os.system(bashCommand)

# deploying main contract
import main_contract_spec as MAIN_CONTRACT
abstarct_main_contract = w3.eth.contract(abi=MAIN_CONTRACT.abi, bytecode=MAIN_CONTRACT.bytecode)
tx_hash = abstarct_main_contract.constructor().transact({'value': w3.toWei(1, 'gwei'), 'from': w3.eth.accounts[0], 'gas': 2100000000})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
assert(tx_receipt.status == 1)
print("* Main contract deployed at", tx_receipt.contractAddress)

main_contract = w3.eth.contract(address=tx_receipt.contractAddress, abi=MAIN_CONTRACT.abi)

FILE = "main_contract_spec.py"
with open(FILE, 'a') as f:
    print(f"MAIN_CONTRACT_ADDRESS = '{main_contract.address}'", file=f)

print('''
Now, run the files:
1) "control_room_logger.py"
2) "child_contracts_logger.py"
and one of the files in the "test/" folder. 
''')

input("When done, press Enter to Create Market")
t = time.time()

print("Opening Market.. ", end='')
tx_hash = main_contract.functions.create_market().transact({'from': w3.eth.accounts[0], 'gas': 2100000000})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
assert(tx_receipt.status == 1)
print(f"done in {'%.0f' % (time.time() - t)} seconds")

input("\nAfter all orders are received (large/small users), press Enter to trigger Gate Closure")
t = time.time()

print("Gate closure.. ", end='')
# the TSO can decide to trigger all together or any combination of the child smart contracts
tx_hash = main_contract.functions.trigger_gate_closure([True, False, False]).transact({'from': w3.eth.accounts[0], 'gas': 2100000000})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
assert(tx_receipt.status == 1)

tx_hash = main_contract.functions.trigger_gate_closure([False, True, False]).transact({'from': w3.eth.accounts[0], 'gas': 2100000000})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
assert(tx_receipt.status == 1)

tx_hash = main_contract.functions.trigger_gate_closure([False, False, True]).transact({'from': w3.eth.accounts[0], 'gas': 2100000000})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
assert(tx_receipt.status == 1)
print(f"done in {'%.0f' % (time.time() - t)} seconds. The received bids are in the file 'collected_bids.xlsx'.")

input("\nPress Enter to send accepted bids (file 'accepted_bids.xlsx')")
t = time.time()

df = pd.read_excel(r'accepted_bids.xlsx')

print('Sending accepted bids.. ', end='')
for bid_id,ref,sett_p,sender,node,bid_type,price_penny_per_kWh,quantity_kW in zip(df['bid_id'], df['ref'], df['sett_p'], df['sender'], df['node'], df['bid_type'], df['price_penny_per_kWh'], df['quantity_kW']):

    # print(bid_id,ref,sett_p,sender,node,bid_type,price_penny_per_kWh,quantity_kW)
    if quantity_kW == 0:  # order not accepted
        continue

    tx_hash = main_contract.functions.submit_accepted_orders(bid_id,ref,sett_p,sender,node,bid_type,price_penny_per_kWh,quantity_kW).transact({'from': w3.eth.accounts[0], 'gas': 21000000000})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    assert(tx_receipt.status)

main_contract.functions.log_accepted_bids_submitted().transact({'from': w3.eth.accounts[0], 'gas': 2100000000})

print(f"done in {'%.0f' % (time.time() - t)} seconds.")


