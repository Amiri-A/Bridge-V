from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware 
from datetime import datetime
import json
import pandas as pd


def connect_to(chain):
    if chain == 'source':  # Source contract on Avalanche
        api_url = "https://api.avax-test.network/ext/bc/C/rpc"
    if chain == 'destination':  # Destination contract on BNB
        api_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"
    
  
    w3 = Web3(Web3.HTTPProvider(api_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3

def get_contract_info(chain, contract_info="contract_info.json"):
    with open(contract_info, 'r') as f:
        contracts = json.load(f)
    return contracts[chain]

def scan_blocks(chain, contract_info="contract_info.json"):
    if chain not in ['source', 'destination']:
        print(f"Invalid chain: {chain}")
        return 0
    
    #TO DO, MY CODE HERE

    source_w3 = connect_to('source')
    destination_w3 = connect_to('destination')
    
    contracts_source = get_contract_info('source', contract_info)
    contracts_destination = get_contract_info('destination', contract_info)
    
    contract_source_address = contracts_source['address']
    contract_source_abi = contracts_source['abi']
    contract_destination_address = contracts_destination['address']
    contract_destination_abi = contracts_destination['abi']
    
    source_contract = source_w3.eth.contract(address=contract_source_address, abi=contract_source_abi)
    destination_contract = destination_w3.eth.contract(address=contract_destination_address, abi=contract_destination_abi)
    
    start_block = source_w3.eth.get_block_number() - 10
    end_block = source_w3.eth.get_block_number()

    acct = source_w3.eth.account.from_key('b55d023def3b04912953e0ed6a059eccfdadf066de0a4e8b8a8f3bde95c80461')

    if chain == "source":
        
        event_name = "Deposit"
        event_filter = source_contract.events[event_name].create_filter(from_block=start_block, to_block=end_block)
        events = event_filter.get_all_entries()

        nonce = destination_w3.eth.get_transaction_count(acct.address)
        for evt in events:
            print(f"Found Deposit event on source: {evt}")
            token = evt.args['token']
            amount = evt.args['amount']
            recipient = evt.args['recipient']
            

            transaction = destination_contract.functions.wrap(token, recipient, amount).build_transaction({
                'from': acct.address,
                'gas': 100000,  
                'gasPrice': destination_w3.eth.gas_price,
                'nonce': nonce
            })
            nonce += 1
            signed_txn = destination_w3.eth.account.sign_transaction(transaction, private_key=acct.key)
            destination_w3.eth.send_raw_transaction(signed_txn.raw_transaction)

    elif chain == "destination":
        
        event_name = "Unwrap"
        event_filter = destination_contract.events[event_name].create_filter(from_block=start_block, to_block=end_block)
        events = event_filter.get_all_entries()

        nonce = source_w3.eth.get_transaction_count(acct.address)
        for evt in events:
            print(f"Found Unwrap event on destination: {evt}")
            token = evt.args['underlying_token']
            amount = evt.args['amount']
            recipient = evt.args['to']
            
            
            transaction = source_contract.functions.withdraw(token, recipient, amount).build_transaction({
                'from': acct.address,
                'gas': 100000,  
                'gasPrice': source_w3.eth.gas_price,
                'nonce': nonce
            })
            nonce += 1
            signed_txn = source_w3.eth.account.sign_transaction(transaction, private_key=acct.key)
            source_w3.eth.send_raw_transaction(signed_txn.raw_transaction)


# scan_blocks('source', contract_info="contract_info.json")
# scan_blocks('destination', contract_info="contract_info.json")
