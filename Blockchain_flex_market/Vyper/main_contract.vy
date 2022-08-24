# @version ^0.3.1

#import aggregator_template as aggregator_template
interface aggregator_template:
    def initialize(sett_p: uint256, node: String[10], wei_in_one_hundredth_of_a_penny: uint256): nonpayable
    def trigger_gate_closure(): nonpayable
    def submit_accepted_orders(bid_id: uint256, ref: uint256, sett_p: uint256, sender: address, node: String[10],
                               bid_type: String[4], price_penny_per_kWh: uint256, accepted_quantity_kW: uint256): nonpayable

AGGREGATOR_TEMPLATE_ADDRESS: constant(address) = 0x49e79fe3855a64dE2a72fdC32AfB2fC74985B992
MAX_BID_COUNT: constant(uint256) = 100 + 2  # large users + orders from child contracts

owner: address
wei_in_one_hundredth_of_a_penny: uint256  # how many wei in one hundredth of a penny, used to compute payments

sett_p: uint256
node1: String[10]
node2: String[10]
node3: String[10]
deployed_aggregator_address_list: HashMap[String[10], address]

market_open: bool
gate_closure: bool

struct bid:
    bid_id: uint256
    ref: uint256
    sett_p: uint256
    sender: address
    node: String[10]
    bid_type: String[4]
    price_penny_per_kWh: uint256
    quantity_kW: uint256 

bid_count: uint256
bids: bid[MAX_BID_COUNT]
accepted_bids: bid[MAX_BID_COUNT]

event open_market:
    sett_p: uint256
    node1: String[10]
    node2: String[10]
    node3: String[10]
    deployed_agg_node1_address: address # HashMap can only be storage type
    deployed_agg_node2_address: address
    deployed_agg_node3_address: address

event received_bid:
    bid_id: uint256
    ref: uint256
    sett_p: uint256
    sender: address
    node: String[10]
    bid_type: String[4]
    price_penny_per_kWh: uint256
    quantity_kW: uint256 

event accepted_bid: 
    bid_id: uint256
    ref: uint256 
    sett_p: uint256
    sender: address
    node: String[10]
    bid_type: String[4]
    price_penny_per_kWh: uint256
    quantity_kW: uint256 

event gate_closure:
    pass

event accepted_bids_submitted:
    pass

event paid:
    sender: address
    ref: uint256
    price_penny_per_kWh: uint256 
    metered_quantity_kW: uint256
    expected_quantity_kW: uint256
    to_pay_in_hundredths_of_a_penny: uint256

event paid_agg:
    sender: address
    ref: uint256
    price_penny_per_kWh: uint256 
    metered_quantity_kW: decimal
    expected_quantity_kW: uint256
    to_pay_in_hundredths_of_a_penny: uint256


@external
def __init__():
    self.owner = msg.sender


@external
def create_market(sett_p: uint256 = 1, node1: String[10] = 'a', node2: String[10] = 'b', node3: String[10] = 'c',
                  wei_in_one_hundredth_of_a_penny: uint256 = 1):

    assert (msg.sender == self.owner)

    self.sett_p = sett_p 
    self.node1 = node1
    self.node2 = node2
    self.node3 = node3
    self.wei_in_one_hundredth_of_a_penny = wei_in_one_hundredth_of_a_penny

    # creating child smart contracts
    self.deployed_aggregator_address_list[self.node1] = create_forwarder_to(AGGREGATOR_TEMPLATE_ADDRESS)
    self.deployed_aggregator_address_list[self.node2] = create_forwarder_to(AGGREGATOR_TEMPLATE_ADDRESS)
    self.deployed_aggregator_address_list[self.node3] = create_forwarder_to(AGGREGATOR_TEMPLATE_ADDRESS)

    # initialize child smart contracts
    aggregator_template(self.deployed_aggregator_address_list[self.node1]).initialize(self.sett_p, self.node1, self.wei_in_one_hundredth_of_a_penny)
    aggregator_template(self.deployed_aggregator_address_list[self.node2]).initialize(self.sett_p, self.node2, self.wei_in_one_hundredth_of_a_penny)
    aggregator_template(self.deployed_aggregator_address_list[self.node3]).initialize(self.sett_p, self.node3, self.wei_in_one_hundredth_of_a_penny)

    # child smart contracts' initial endowment
    send(self.deployed_aggregator_address_list[self.node1], 10000)
    send(self.deployed_aggregator_address_list[self.node2], 10000)
    send(self.deployed_aggregator_address_list[self.node3], 10000)

    # clear previous data
    for i in range(0, MAX_BID_COUNT):
        if i == self.bid_count:
            break
        self.bids[i] = empty(bid)
        self.accepted_bids[i] = empty(bid)
    
    self.bid_count = 0

    # create event log
    log open_market(self.sett_p, self.node1, self.node2, self.node3, 
                    self.deployed_aggregator_address_list[self.node1], self.deployed_aggregator_address_list[self.node2],
                    self.deployed_aggregator_address_list[self.node3])

    # start market session    
    self.market_open = True
    self.gate_closure = False


@external
def submit_bid(ref: uint256, sett_p: uint256, node: String[10], bid_type: String[4], price_penny_per_kWh: uint256, quantity_kW: uint256):

    assert(self.market_open)
    assert(self.bid_count < MAX_BID_COUNT)
    assert(sett_p == self.sett_p)
    assert(node in [self.node1, self.node2, self.node3])

    self.bids[self.bid_count].bid_id = self.bid_count
    self.bids[self.bid_count].ref = ref
    self.bids[self.bid_count].sett_p = sett_p
    self.bids[self.bid_count].sender = msg.sender
    self.bids[self.bid_count].node = node
    self.bids[self.bid_count].bid_type = bid_type
    self.bids[self.bid_count].price_penny_per_kWh = price_penny_per_kWh
    self.bids[self.bid_count].quantity_kW = quantity_kW

    log received_bid(self.bids[self.bid_count].bid_id, self.bids[self.bid_count].ref, self.bids[self.bid_count].sett_p,
                     self.bids[self.bid_count].sender, self.bids[self.bid_count].node, self.bids[self.bid_count].bid_type,
                     self.bids[self.bid_count].price_penny_per_kWh, self.bids[self.bid_count].quantity_kW)

    self.bid_count += 1

nodes_closed: bool[3]
@external
def trigger_gate_closure(nodes_closed: bool[3]):
    assert(msg.sender == self.owner)
    assert(self.market_open)

    if nodes_closed[0] and self.nodes_closed[0] == False:
        self.nodes_closed[0] = True
        aggregator_template(self.deployed_aggregator_address_list[self.node1]).trigger_gate_closure()
    
    if nodes_closed[1] and self.nodes_closed[1] == False:
        self.nodes_closed[1] = True
        aggregator_template(self.deployed_aggregator_address_list[self.node2]).trigger_gate_closure()

    if nodes_closed[2] and self.nodes_closed[2] == False:
        self.nodes_closed[2] = True
        aggregator_template(self.deployed_aggregator_address_list[self.node3]).trigger_gate_closure()

    if (self.nodes_closed[0] == True) and (self.nodes_closed[1] == True) and (self.nodes_closed[2] == True):      
        self.market_open = False
        self.gate_closure = True
        log gate_closure()


@external
def submit_accepted_orders(bid_id: uint256, ref: uint256, sett_p: uint256, sender: address, node: String[10],
                           bid_type: String[4], price_penny_per_kWh: uint256, accepted_quantity_kW: uint256):

    assert(msg.sender == self.owner)
    assert(self.gate_closure)

    assert(ref == self.bids[bid_id].ref)
    assert(sett_p == self.bids[bid_id].sett_p)
    assert(sender == self.bids[bid_id].sender)
    assert(node == self.bids[bid_id].node)
    assert(bid_type == self.bids[bid_id].bid_type)
    assert(price_penny_per_kWh == self.bids[bid_id].price_penny_per_kWh)
    assert(accepted_quantity_kW <= self.bids[bid_id].quantity_kW)

    self.accepted_bids[bid_id] = self.bids[bid_id]
    self.accepted_bids[bid_id].quantity_kW = accepted_quantity_kW

    # broadcast to child smart contracts
    if sender in [self.deployed_aggregator_address_list[self.node1], self.deployed_aggregator_address_list[self.node2], 
                  self.deployed_aggregator_address_list[self.node3]]:
        aggregator_template(sender).submit_accepted_orders(bid_id, ref, sett_p, sender, node, bid_type, price_penny_per_kWh, accepted_quantity_kW)

    log accepted_bid(self.accepted_bids[bid_id].bid_id, self.accepted_bids[bid_id].ref, self.accepted_bids[bid_id].sett_p, 
                     self.accepted_bids[bid_id].sender, self.accepted_bids[bid_id].node, self.accepted_bids[bid_id].bid_type,
                     self.accepted_bids[bid_id].price_penny_per_kWh, self.accepted_bids[bid_id].quantity_kW)


@external
def log_accepted_bids_submitted():

    assert(msg.sender == self.owner)
    assert(self.gate_closure)

    log accepted_bids_submitted()    


@external
@nonreentrant("lock")
def submit_metered_data_and_pay(bid_id: uint256, ref: uint256, sett_p: uint256, sender: address, node: String[10],
                                bid_type: String[4], price_penny_per_kWh: uint256, metered_quantity_kW: uint256, agg_avg_metered: decimal = 0.0) -> decimal:

    assert(sender == msg.sender)
    assert(sender == self.accepted_bids[bid_id].sender)
    assert(block.timestamp > sett_p)

    assert(ref == self.accepted_bids[bid_id].ref)
    assert(sett_p == self.accepted_bids[bid_id].sett_p)
    assert(node == self.accepted_bids[bid_id].node)
    assert(bid_type == self.accepted_bids[bid_id].bid_type)
    assert(price_penny_per_kWh == self.accepted_bids[bid_id].price_penny_per_kWh)

    met_quantity_kW: decimal = convert(metered_quantity_kW, decimal)
    
    if sender in [self.deployed_aggregator_address_list[self.node1], self.deployed_aggregator_address_list[self.node2], 
                  self.deployed_aggregator_address_list[self.node3]]:
                  assert agg_avg_metered != 0.0, "agg_avg_metered != 0.0"
                  met_quantity_kW = agg_avg_metered
    
    exp_quantity_kW: decimal = convert(self.accepted_bids[bid_id].quantity_kW, decimal)
    
    payment_without_penalty: decimal = convert(price_penny_per_kWh, decimal)*met_quantity_kW*0.5  # half-hour periods
    imbalance: decimal = 0.0
    penalty_factor: decimal = 0.0

    if met_quantity_kW >= exp_quantity_kW:
        imbalance = (met_quantity_kW - exp_quantity_kW)/exp_quantity_kW
    else:
        imbalance = (exp_quantity_kW - met_quantity_kW)/exp_quantity_kW     

    if 0.0 <= imbalance and imbalance <= 0.10:
        penalty_factor = 0.0
    elif imbalance <= 0.50:
        penalty_factor = 0.5
    else:
        penalty_factor = 1.0

    to_pay_in_hundredths_of_a_penny: uint256 = convert(payment_without_penalty*(1.0 - penalty_factor)*100.0, uint256)

    if sender in [self.deployed_aggregator_address_list[self.node1], self.deployed_aggregator_address_list[self.node2], 
                  self.deployed_aggregator_address_list[self.node3]]:
        log paid_agg(sender, ref, price_penny_per_kWh, agg_avg_metered, self.accepted_bids[bid_id].quantity_kW, to_pay_in_hundredths_of_a_penny)          
    else:
        log paid(sender, ref, price_penny_per_kWh, metered_quantity_kW, self.accepted_bids[bid_id].quantity_kW, to_pay_in_hundredths_of_a_penny)

    self.accepted_bids[bid_id] = empty(bid)

    # here we assume that the metered data comes from a tamper-proof device and is trustworthy
    send(sender, to_pay_in_hundredths_of_a_penny*self.wei_in_one_hundredth_of_a_penny)

    return payment_without_penalty*penalty_factor


event payment_received:
    sender: address
    value: uint256

@external
@payable
def __default__():
    log payment_received(msg.sender, msg.value)

