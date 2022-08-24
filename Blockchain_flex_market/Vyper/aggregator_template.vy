# @version ^0.3.1

interface main_contract:
    def submit_bid(ref: uint256, sett_p: uint256, node: String[10], bid_type: String[4], price_penny_per_kWh: uint256, quantity_kW: uint256): nonpayable
    def submit_metered_data_and_pay(bid_id: uint256, ref: uint256, sett_p: uint256, sender: address, node: String[10],
                                bid_type: String[4], price_penny_per_kWh: uint256, metered_quantity_kW: uint256, agg_avg_metered: decimal) -> decimal: nonpayable

MAX_BID_COUNT: constant(uint256) = 100  # max number of bids

owner: address
market_open: bool
gate_closure: bool
sett_p: uint256
node: String[10]
wei_in_one_hundredth_of_a_penny: uint256

struct bid:
    bid_id: uint256
    ref: uint256
    sett_p: uint256
    sender: address
    node: String[10]
    bid_type: String[4]
    price_penny_per_kWh: uint256
    quantity_kW: uint256
    t1: uint256 
    t2: uint256 

bid_count: uint256
bids: bid[MAX_BID_COUNT]

event received_bid:
    bid_id: uint256
    ref: uint256
    sett_p: uint256
    sender: address
    node: String[10]
    bid_type: String[4]
    price_penny_per_kWh: uint256
    quantity_kW: uint256
    t1: uint256 
    t2: uint256 


@external
def initialize(sett_p: uint256, node: String[10], wei_in_one_hundredth_of_a_penny: uint256): # no __init__() as create_forwarder_to() does not trigger it
    self.owner = msg.sender
    self.sett_p = sett_p
    self.node = node
    self.market_open = True
    self.gate_closure = False
    self.bid_count = 0
    self.index = empty(uint256[2])
    self.accepted_bid_list_index = 0
    self.wei_in_one_hundredth_of_a_penny = wei_in_one_hundredth_of_a_penny

    for i in range(0, MAX_BID_COUNT):
        self.accepted_bid_list[i] = MAX_BID_COUNT


@external
def aggregator_submit_bid(ref: uint256, sett_p: uint256, node: String[10], bid_type: String[4], price_penny_per_kWh: uint256, quantity_kW: uint256,
                              t1: uint256, t2: uint256 ):

    assert(self.market_open)
    assert(self.bid_count < MAX_BID_COUNT)
    assert(sett_p == self.sett_p)
    assert(node == self.node)
    assert(t1 >= 0 and t2 <= 29)

    self.bids[self.bid_count].bid_id = self.bid_count
    self.bids[self.bid_count].ref = ref
    self.bids[self.bid_count].sett_p = sett_p
    self.bids[self.bid_count].sender = msg.sender
    self.bids[self.bid_count].node = node
    self.bids[self.bid_count].bid_type = bid_type
    self.bids[self.bid_count].price_penny_per_kWh = price_penny_per_kWh
    self.bids[self.bid_count].quantity_kW = quantity_kW
    self.bids[self.bid_count].t1 = t1
    self.bids[self.bid_count].t2 = t2
    

    log received_bid(self.bids[self.bid_count].bid_id, self.bids[self.bid_count].ref, self.bids[self.bid_count].sett_p,
                     self.bids[self.bid_count].sender, self.bids[self.bid_count].node, self.bids[self.bid_count].bid_type,
                     self.bids[self.bid_count].price_penny_per_kWh, self.bids[self.bid_count].quantity_kW,
                     self.bids[self.bid_count].t1, self.bids[self.bid_count].t2)

    self.bid_count += 1


TYPE_UP: constant(uint256) = 0
TYPE_DOWN: constant(uint256) = 1
sorted_list: uint256[MAX_BID_COUNT][2]  # in Vyper multiarray are declared with reverse index order 
index: uint256[2]
aggregated_bid: bid[2]
MAX_price_penny_per_kWh: constant(uint256) = 100

event log_profile:
    bid_id: uint256
    ref: uint256
    sett_p: uint256
    sender: address
    node: String[10]
    bid_type: String[4]
    price_penny_per_kWh: uint256
    t0: uint256 
    t1: uint256
    t2: uint256 
    t3: uint256
    t4: uint256 
    t5: uint256
    t6: uint256 
    t7: uint256
    t8: uint256 
    t9: uint256
    t10: uint256 
    t11: uint256
    t12: uint256 
    t13: uint256
    t14: uint256 
    t15: uint256
    t16: uint256 
    t17: uint256
    t18: uint256 
    t19: uint256
    t20: uint256 
    t21: uint256
    t22: uint256 
    t23: uint256
    t24: uint256 
    t25: uint256
    t26: uint256 
    t27: uint256
    t28: uint256 
    t29: uint256

@external
def trigger_gate_closure():
    assert(msg.sender == self.owner)
    assert(self.market_open)

    bid_type: String[4] = ''
    for c in [TYPE_UP, TYPE_DOWN]:

        if c == TYPE_UP:
            bid_type = 'up'
        else:
            bid_type = 'down'            

        for price_penny_per_kWh in range(0, MAX_price_penny_per_kWh + 1):
            for i in range(0, MAX_BID_COUNT):
                if i == self.bid_count:
                    break
                if self.bids[i].bid_type != bid_type:
                    continue
                if price_penny_per_kWh == self.bids[i].price_penny_per_kWh:
                    self.sorted_list[c][self.index[c]] = i
                    self.index[c] += 1

        x: uint256[30] = empty(uint256[30])
        for i in range(0, MAX_BID_COUNT):
            if i == self.bid_count:
                break
            if self.bids[i].bid_type != bid_type:
                continue
            for t in range(0, 30):          
                if self.bids[i].t1 <= t and t <= self.bids[i].t2:
                    x[t] += self.bids[i].quantity_kW

        sustainable_kW: uint256 = MAX_UINT256
        for t in range(0, 30):        
            sustainable_kW = min(x[t], sustainable_kW)

        if sustainable_kW > 0:

            aggregated_quantity: uint256[30] = empty(uint256[30])
            avg_price_penny_per_kWh: uint256 = 0  # working with decimal creates compatibility problems with web3py
            start_profiles: uint256[30][MAX_BID_COUNT] = empty(uint256[30][MAX_BID_COUNT])  # multiarray: reverse index order! 
            for t in range(0, 30):
                for i in range(0, MAX_BID_COUNT):
                    if i == self.index[c]:
                        break
                    if self.bids[self.sorted_list[c][i]].t1 <= t and t <= self.bids[self.sorted_list[c][i]].t2:
                        if aggregated_quantity[t] + self.bids[self.sorted_list[c][i]].quantity_kW <= sustainable_kW:
                            aggregated_quantity[t] += self.bids[self.sorted_list[c][i]].quantity_kW
                            start_profiles[self.sorted_list[c][i]][t] = self.bids[self.sorted_list[c][i]].quantity_kW
                            avg_price_penny_per_kWh += self.bids[self.sorted_list[c][i]].quantity_kW * self.bids[self.sorted_list[c][i]].price_penny_per_kWh
                        elif aggregated_quantity[t] < sustainable_kW:
                            start_profiles[self.sorted_list[c][i]][t] = sustainable_kW - aggregated_quantity[t]
                            avg_price_penny_per_kWh += (sustainable_kW - aggregated_quantity[t]) * self.bids[self.sorted_list[c][i]].price_penny_per_kWh
                            break
                        
            avg_price_dec: decimal = convert(avg_price_penny_per_kWh, decimal)/convert(sustainable_kW, decimal)/30.0
            avg_price_penny_per_kWh = convert(avg_price_dec + 0.5, uint256)  # +0.5 to round() instead of floor()

            for i in range(0, MAX_BID_COUNT):
                if i == self.index[c]:
                    break
                log log_profile(self.bids[self.sorted_list[c][i]].bid_id, self.bids[self.sorted_list[c][i]].ref, self.bids[self.sorted_list[c][i]].sett_p,
                            self.bids[self.sorted_list[c][i]].sender, self.bids[self.sorted_list[c][i]].node, self.bids[self.sorted_list[c][i]].bid_type,
                            self.bids[self.sorted_list[c][i]].price_penny_per_kWh, start_profiles[self.sorted_list[c][i]][0], start_profiles[self.sorted_list[c][i]][1], 
                            start_profiles[self.sorted_list[c][i]][2], start_profiles[self.sorted_list[c][i]][3], start_profiles[self.sorted_list[c][i]][4], 
                            start_profiles[self.sorted_list[c][i]][5], start_profiles[self.sorted_list[c][i]][6], start_profiles[self.sorted_list[c][i]][7], 
                            start_profiles[self.sorted_list[c][i]][8], start_profiles[self.sorted_list[c][i]][9], start_profiles[self.sorted_list[c][i]][10],
                            start_profiles[self.sorted_list[c][i]][11], start_profiles[self.sorted_list[c][i]][12], start_profiles[self.sorted_list[c][i]][13],
                            start_profiles[self.sorted_list[c][i]][14], start_profiles[self.sorted_list[c][i]][15], start_profiles[self.sorted_list[c][i]][16], 
                            start_profiles[self.sorted_list[c][i]][17], start_profiles[self.sorted_list[c][i]][18], start_profiles[self.sorted_list[c][i]][19],
                            start_profiles[self.sorted_list[c][i]][20], start_profiles[self.sorted_list[c][i]][21], start_profiles[self.sorted_list[c][i]][22], 
                            start_profiles[self.sorted_list[c][i]][23], start_profiles[self.sorted_list[c][i]][24], start_profiles[self.sorted_list[c][i]][25], 
                            start_profiles[self.sorted_list[c][i]][26], start_profiles[self.sorted_list[c][i]][27], start_profiles[self.sorted_list[c][i]][28],
                            start_profiles[self.sorted_list[c][i]][29]) 

            self.aggregated_bid[c].ref = c
            self.aggregated_bid[c].sett_p = self.sett_p 
            self.aggregated_bid[c].sender = self
            self.aggregated_bid[c].node = self.node
            self.aggregated_bid[c].bid_type = bid_type
            self.aggregated_bid[c].price_penny_per_kWh = avg_price_penny_per_kWh
            self.aggregated_bid[c].quantity_kW = sustainable_kW

            main_contract(self.owner).submit_bid(c, self.sett_p, self.node, bid_type, avg_price_penny_per_kWh, sustainable_kW)
    
    self.market_open = False
    self.gate_closure = True


accepted_aggregated_bid: bid[2]
accepted_profiles: uint256[30][MAX_BID_COUNT]  # mutiarray in reverse index order

event log_accepted_profile:
    bid_id: uint256
    ref: uint256
    sett_p: uint256
    sender: address
    node: String[10]
    bid_type: String[4]
    price_penny_per_kWh: uint256
    t0: uint256 
    t1: uint256
    t2: uint256 
    t3: uint256
    t4: uint256 
    t5: uint256
    t6: uint256 
    t7: uint256
    t8: uint256 
    t9: uint256
    t10: uint256 
    t11: uint256
    t12: uint256 
    t13: uint256
    t14: uint256 
    t15: uint256
    t16: uint256 
    t17: uint256
    t18: uint256 
    t19: uint256
    t20: uint256 
    t21: uint256
    t22: uint256 
    t23: uint256
    t24: uint256 
    t25: uint256
    t26: uint256 
    t27: uint256
    t28: uint256 
    t29: uint256

accepted_bid_list: uint256[MAX_BID_COUNT]
accepted_bid_list_index: uint256

@external
def submit_accepted_orders(bid_id: uint256, ref: uint256, sett_p: uint256, sender: address, node: String[10],
                           bid_type: String[4], price_penny_per_kWh: uint256, accepted_quantity_kW: uint256):

    assert(msg.sender == self.owner)
    assert(sender == self)
    assert(self.gate_closure)
    
    c: uint256 = ref

    assert(ref == self.aggregated_bid[c].ref)
    assert(sett_p == self.aggregated_bid[c].sett_p)
    assert(sender == self.aggregated_bid[c].sender)
    assert(node == self.aggregated_bid[c].node)
    assert(bid_type == self.aggregated_bid[c].bid_type)
    assert(price_penny_per_kWh == self.aggregated_bid[c].price_penny_per_kWh)
    assert(accepted_quantity_kW <= self.aggregated_bid[c].quantity_kW)

    self.accepted_aggregated_bid[c] = self.aggregated_bid[c]
    self.accepted_aggregated_bid[c].bid_id = bid_id
    self.accepted_aggregated_bid[c].quantity_kW = accepted_quantity_kW

    aggregated_quantity: uint256[30] = empty(uint256[30])
    for t in range(0, 30):
        for i in range(0, MAX_BID_COUNT):
            if i == self.index[c]:
                break
            if self.bids[self.sorted_list[c][i]].t1 <= t and t <= self.bids[self.sorted_list[c][i]].t2:
                if aggregated_quantity[t] + self.bids[self.sorted_list[c][i]].quantity_kW <= accepted_quantity_kW:
                    aggregated_quantity[t] += self.bids[self.sorted_list[c][i]].quantity_kW
                    self.accepted_profiles[self.sorted_list[c][i]][t] = self.bids[self.sorted_list[c][i]].quantity_kW
                    if self.bids[self.sorted_list[c][i]].bid_id not in self.accepted_bid_list:
                        self.accepted_bid_list[self.accepted_bid_list_index] = self.bids[self.sorted_list[c][i]].bid_id
                        self.accepted_bid_list_index += 1
                elif aggregated_quantity[t] < accepted_quantity_kW:
                    self.accepted_profiles[self.sorted_list[c][i]][t] = accepted_quantity_kW - aggregated_quantity[t]
                    if self.bids[self.sorted_list[c][i]].bid_id not in self.accepted_bid_list:
                        self.accepted_bid_list[self.accepted_bid_list_index] = self.bids[self.sorted_list[c][i]].bid_id
                        self.accepted_bid_list_index += 1
                    break
    
    for i in range(0, MAX_BID_COUNT):
        if i == self.index[c]:
            break
        log log_accepted_profile(
                    self.bids[self.sorted_list[c][i]].bid_id, self.bids[self.sorted_list[c][i]].ref, self.bids[self.sorted_list[c][i]].sett_p,
                    self.bids[self.sorted_list[c][i]].sender, self.bids[self.sorted_list[c][i]].node, self.bids[self.sorted_list[c][i]].bid_type,
                    self.bids[self.sorted_list[c][i]].price_penny_per_kWh, self.accepted_profiles[self.sorted_list[c][i]][0], self.accepted_profiles[self.sorted_list[c][i]][1], 
                    self.accepted_profiles[self.sorted_list[c][i]][2], self.accepted_profiles[self.sorted_list[c][i]][3], self.accepted_profiles[self.sorted_list[c][i]][4], 
                    self.accepted_profiles[self.sorted_list[c][i]][5], self.accepted_profiles[self.sorted_list[c][i]][6], self.accepted_profiles[self.sorted_list[c][i]][7], 
                    self.accepted_profiles[self.sorted_list[c][i]][8], self.accepted_profiles[self.sorted_list[c][i]][9], self.accepted_profiles[self.sorted_list[c][i]][10],
                    self.accepted_profiles[self.sorted_list[c][i]][11], self.accepted_profiles[self.sorted_list[c][i]][12], self.accepted_profiles[self.sorted_list[c][i]][13],
                    self.accepted_profiles[self.sorted_list[c][i]][14], self.accepted_profiles[self.sorted_list[c][i]][15], self.accepted_profiles[self.sorted_list[c][i]][16], 
                    self.accepted_profiles[self.sorted_list[c][i]][17], self.accepted_profiles[self.sorted_list[c][i]][18], self.accepted_profiles[self.sorted_list[c][i]][19],
                    self.accepted_profiles[self.sorted_list[c][i]][20], self.accepted_profiles[self.sorted_list[c][i]][21], self.accepted_profiles[self.sorted_list[c][i]][22], 
                    self.accepted_profiles[self.sorted_list[c][i]][23], self.accepted_profiles[self.sorted_list[c][i]][24], self.accepted_profiles[self.sorted_list[c][i]][25], 
                    self.accepted_profiles[self.sorted_list[c][i]][26], self.accepted_profiles[self.sorted_list[c][i]][27], self.accepted_profiles[self.sorted_list[c][i]][28],
                    self.accepted_profiles[self.sorted_list[c][i]][29]) 


event send_agg_meter:
    bid_id: uint256
    ref: uint256
    sett_p: uint256
    sender: address
    node: String[10]
    bid_type: String[4]
    price_penny_per_kWh: uint256
    agg_avg_metered: decimal

event payment_received:
    sender: address
    value: uint256

@external
@payable
def __default__():
    log payment_received(msg.sender, msg.value)

metered_agg_power: uint256[2]

imbalance: uint256[MAX_BID_COUNT]
imbalance_tot: uint256[2]
imbalance_share: decimal[MAX_BID_COUNT]

metered_indiv_power: uint256[MAX_BID_COUNT]

sender_received: address[MAX_BID_COUNT]

received: uint256

event log_received_metered:
    bid_id: uint256
    ref: uint256
    sett_p: uint256
    node: String[10]
    bid_type: String[4]
    price_penny_per_kWh: uint256
    metered: uint256[30]

event pay_small_user:
    bid_id: uint256
    ref: uint256
    sender: address
    price_penny_per_kWh: uint256
    metered_indiv_power: uint256
    metered_pay: uint256
    penality: decimal 
    imbalance: uint256
    imbalance_tot: uint256
    imbalance_share: decimal
    individual_penality: uint256
    to_pay_in_hundredths_of_a_penny: int256


event  my_log:
    val: decimal


@external
def agg_submit_metered_data(bid_id: uint256, ref: uint256, sett_p: uint256, sender: address, node: String[10],
                            bid_type: String[4], price_penny_per_kWh: uint256, metered: uint256[30]):

    assert(sender == msg.sender)
    assert(block.timestamp > sett_p)
    assert(bid_id in self.accepted_bid_list)
    assert(self.gate_closure)
    assert(sender != ZERO_ADDRESS)

    assert(ref == self.bids[bid_id].ref)
    assert(sett_p == self.bids[bid_id].sett_p)
    assert(sender == self.bids[bid_id].sender)
    assert(node == self.bids[bid_id].node)
    assert(bid_type == self.bids[bid_id].bid_type)
    assert(price_penny_per_kWh == self.bids[bid_id].price_penny_per_kWh)
    
    # prevent double payments
    self.sender_received[bid_id] = self.bids[bid_id].sender
    self.bids[bid_id].sender = ZERO_ADDRESS

    log log_received_metered(bid_id, ref, sett_p, node, bid_type, price_penny_per_kWh, metered)

    c: uint256 = 0
    if bid_type == 'up':
        c = TYPE_UP
    else:
        c = TYPE_DOWN
    
    for t in range(0, 30):
        self.metered_indiv_power[bid_id] += metered[t]
        
        self.metered_agg_power[c] += metered[t]
       
        if self.accepted_profiles[bid_id][t] > metered[t]:
            self.imbalance[bid_id] += self.accepted_profiles[bid_id][t] - metered[t]
        else:
            self.imbalance[bid_id] += metered[t] - self.accepted_profiles[bid_id][t]
    self.imbalance_tot[c] += self.imbalance[bid_id]

    self.received += 1

    if self.received == self.accepted_bid_list_index:
        penality: decimal[2] = [0.0, 0.0]

        for cc in [TYPE_UP, TYPE_DOWN]:
            if self.accepted_aggregated_bid[cc].quantity_kW != 0:
                agg_avg_metered: decimal = convert(self.metered_agg_power[cc], decimal) / 30.0

                log send_agg_meter(
                                    self.accepted_aggregated_bid[cc].bid_id,
                                    self.accepted_aggregated_bid[cc].ref, 
                                    self.accepted_aggregated_bid[cc].sett_p, 
                                    self.accepted_aggregated_bid[cc].sender, 
                                    self.accepted_aggregated_bid[cc].node, 
                                    self.accepted_aggregated_bid[cc].bid_type, 
                                    self.accepted_aggregated_bid[cc].price_penny_per_kWh, 
                                    agg_avg_metered
                                )

                penality[cc] = main_contract(self.owner).submit_metered_data_and_pay(
                                            self.accepted_aggregated_bid[cc].bid_id,
                                            self.accepted_aggregated_bid[cc].ref, 
                                            self.accepted_aggregated_bid[cc].sett_p, 
                                            self.accepted_aggregated_bid[cc].sender, 
                                            self.accepted_aggregated_bid[cc].node, 
                                            self.accepted_aggregated_bid[cc].bid_type, 
                                            self.accepted_aggregated_bid[cc].price_penny_per_kWh, 
                                            0, 
                                            agg_avg_metered)
 

        for b_id in self.accepted_bid_list:
            if b_id == MAX_BID_COUNT:
                break

            if self.bids[b_id].bid_type == 'up':
                c = TYPE_UP
            else:
                c = TYPE_DOWN

            if self.imbalance_tot[c] > 0:
                self.imbalance_share[b_id] = convert(self.imbalance[b_id], decimal)/convert(self.imbalance_tot[c], decimal)
            else:
                self.imbalance_share[b_id] = 0.0

            metered_pay: uint256 = (self.metered_indiv_power[b_id] * self.bids[b_id].price_penny_per_kWh * 10**6) / (30*2)   # 1/2 as half-hour periods
            individual_penality: uint256 = convert(penality[c]*self.imbalance_share[b_id]*1000000.0, uint256)
            to_pay_in_hundredths_of_a_penny: int256 = (convert(metered_pay, int256) - convert(individual_penality, int256))*100/10**6
        
            if to_pay_in_hundredths_of_a_penny < 0:
                to_pay_in_hundredths_of_a_penny = 0
        
            log pay_small_user(self.bids[b_id].bid_id, self.bids[b_id].ref, self.sender_received[b_id],
                               self.bids[b_id].price_penny_per_kWh, self.metered_indiv_power[b_id], metered_pay, penality[c],
                               self.imbalance[b_id], self.imbalance_tot[c],
                               self.imbalance_share[b_id], individual_penality, to_pay_in_hundredths_of_a_penny)
            send(self.sender_received[b_id], convert(to_pay_in_hundredths_of_a_penny, uint256)*self.wei_in_one_hundredth_of_a_penny)
        
        selfdestruct(self.owner)

