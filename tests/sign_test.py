#!/usr/bin/env python3
# coding: utf-8
import datetime
import time
import os
import types
import shutil
# from eth_utils import decode_hex
from test_framework import coverage

from conflux.messages import GetBlockHeaders, GET_BLOCK_HEADERS_RESPONSE
from test_framework.mininode import start_p2p_connection
from test_framework.test_framework import ConfluxTestFramework
from test_framework.util import assert_equal, connect_nodes, get_peer_addr, wait_until, WaitHandler, \
    initialize_datadir, PortMin, get_datadir_path, connect_sample_nodes, sync_blocks
from test_framework.blocktools import wait_for_initial_nonce_for_address
import random


class SignTest(ConfluxTestFramework): 
    def __init__(self):
        super().__init__()
        self.nonce_map = {}        

    def set_test_params(self):
        self.num_nodes = 2
        self.conf_parameters = {
            "executive_trace": "true",
            "public_rpc_apis": "\"cfx,debug,test,pubsub,trace\"",
            "mining_type": "'disable'",
        }
        self.conf_parameters["log_level"] = '"trace"'

    def start_node(self, i, extra_args=None, phase_to_wait=["NormalSyncPhase"], wait_time=30, *args, **kwargs):        
        print("start_nodes from this.")
        # only node 1 starts mining
            
        node = self.nodes[i]

        node.start(extra_args, *args, **kwargs)
        node.wait_for_rpc_connection()
        node.wait_for_nodeid()
        # try:
        #     node.pos_start()
        # except Exception as e:
        #     print(e)
        if phase_to_wait is not None:
            node.wait_for_recovery(phase_to_wait, wait_time)

        if self.options.coveragedir is not None:
            coverage.write_all_rpc_commands(self.options.coveragedir, node.rpc)

    def setup_network(self):
        self.setup_nodes()

    def run_test(self):
        time.sleep(7)

        blocks = self.nodes[0].generate_empty_blocks(1)
        self.best_block_hash = blocks[-1] #make_genesis().block_header.hash

        self._test_sign()
        # self._test_quantum_sign()

        time.sleep(5)
        
        self._test_stop()

    def set_genesis_secrets(self):
        genesis_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "./sign_secrets.txt")
        self.conf_parameters["genesis_secrets"] = f"\"{genesis_file_path}\""

    def set_mining(self, node_index):
        if node_index == 1 :
            self.mining_author = "0x10000000000000000000000000000000000000aa"
            self.conf_parameters = {"mining_author": "\"10000000000000000000000000000000000000aa\"",
                        "mining_type": "'cpu'"
                        }
        else:
            self.conf_parameters = {"mining_author": "\"10000000000000000000000000000000000000aa\"",
                        "mining_type": "'disable'"
                        }

    def start_network(self, node_count):
        self.nodes = []
        self.add_nodes(node_count)
        for node_index in range(node_count):
            self.set_mining(node_index)
            self.set_genesis_secrets()
            initialize_datadir(self.options.tmpdir, node_index, PortMin.n, self.conf_parameters)
            self.start_node(node_index, phase_to_wait=None)

        connect_sample_nodes(self.nodes, self.log, sample=self.num_nodes - 1)
        

        sync_blocks(self.nodes)
        for node in self.nodes:
            node.wait_for_recovery(["NormalSyncPhase"], 30)
            
    def _test_sign(self):
        module_name = "test_sign"
        module = __import__("rpc." + module_name, fromlist=True)
        
        obj_type = getattr(module, "TestSignTx") # RpcClient
        obj_type_other_nodes = getattr(module, "TestPool")

        self.stop_nodes()

        # delete nodes' file
        for i in range(len(self.nodes)):
            datadir = get_datadir_path(self.options.tmpdir, i)
            shutil.rmtree(datadir)
        old_pos_files = ["initial_nodes.json", "genesis_file", "waypoint_config", "public_key"]
        for f in old_pos_files:
            os.remove(os.path.join(self.options.tmpdir, f))
        shutil.rmtree(os.path.join(self.options.tmpdir, "private_keys"))

        # start three new nodes and only one execute test method
        self.start_network(3)

        obj = obj_type(self.nodes[0]) # 用其中一个节点的客户端构建交易
        obj_other_nodes_1 = obj_type_other_nodes(self.nodes[1])
        obj_other_nodes_2 = obj_type_other_nodes(self.nodes[2])
        
        # 封装tx
        get_sign_address = getattr(obj, "get_sign_address")
        address = get_sign_address()
        
        tx = self.get_transaction()
        current_nonce = self.get_nonce(address)
        tx["nonce"] = current_nonce



        # method_name = "test_quantum_sign"
        method_name = "test_sign"
        method = getattr(obj, "test_sign")
        self.log.info("TestSignTx" + "." + method_name)

        for i in range(0,1):
            method(tx, address)
            current_nonce = current_nonce + 1
            tx["nonce"] = current_nonce 
            
        # for i in range(0, 10):
        #     tx["value"] = random.randint(0, 20)
        #     print("sign test tx:", tx)
        #     method(tx, address)

        # last check whether tx is in other nodes' pool 

        time.sleep(10)
        method_name = "test_sign_tx_in_pool"
        method_for_node1 = getattr(obj_other_nodes_1, method_name)
        self.log.info("Test whether tx is in other nodes' pool")
        self.log.info("TestPool" + "." + method_name + " for node1")
        method_for_node1()

    def _test_quantum_sign(self):
        module_name = "test_sign"
        module = __import__("rpc." + module_name, fromlist=True)
        
        obj_type = getattr(module, "TestSignTx") # RpcClient
        obj_type_other_nodes = getattr(module, "TestPool")

        self.stop_nodes()

        # delete nodes' file
        for i in range(len(self.nodes)):
            datadir = get_datadir_path(self.options.tmpdir, i)
            shutil.rmtree(datadir)
        old_pos_files = ["initial_nodes.json", "genesis_file", "waypoint_config", "public_key"]
        for f in old_pos_files:
            os.remove(os.path.join(self.options.tmpdir, f))
        shutil.rmtree(os.path.join(self.options.tmpdir, "private_keys"))

        # start three new nodes and only one execute test method
        self.start_network(3)

        obj = obj_type(self.nodes[0]) # 用其中一个节点的客户端构建交易
        obj_other_nodes_1 = obj_type_other_nodes(self.nodes[1])
        obj_other_nodes_2 = obj_type_other_nodes(self.nodes[2])
        
        # 封装tx
        get_quantum_address = getattr(obj, "get_quantum_address")
        address = get_quantum_address()
        # tx_list
        tx = self.get_transaction()
        current_nonce = self.get_nonce(address)
        tx["nonce"] = current_nonce

        method_name = "test_quantum_sign"
        # method_name = "test_sign"
        method = getattr(obj, method_name)
        self.log.info("TestSignTx" + "." + method_name)
        for i in range(0,9):
            method(tx, address)
            current_nonce = current_nonce + 1
            tx["nonce"] = current_nonce 

        # test whether tx is in other nodes' pool 
        method_name = "test_sign_tx_in_pool"
        method_for_node1 = getattr(obj_other_nodes_1, method_name)
        self.log.info("Test whether tx is in other nodes' pool")
        self.log.info("TestPool" + "." + method_name + " for node1")
        method_for_node1()


    # def _test_addlatency(self):
    #     def on_block_headers(node, _):
    #         msec = (datetime.datetime.now() - node.start_time).total_seconds() * 1000
    #         self.log.info("Message arrived after " + str(msec) + "ms")
    #         # The EventLoop in rust may have a deviation of a maximum of
    #         # 100ms. This is because the ticker is 100ms by default.
    #         assert msec >= node.latency_ms - 100

    #     self.log.info("Test addlatency")
    #     block_hash = decode_hex(self.nodes[0].generate_empty_blocks(1)[0])
    #     default_node = start_p2p_connection([self.nodes[0]])[0]
    #     latency_ms = 1000
    #     self.nodes[0].addlatency(default_node.key, latency_ms)
    #     default_node.start_time = datetime.datetime.now()
    #     default_node.latency_ms = latency_ms
    #     handler = WaitHandler(default_node, GET_BLOCK_HEADERS_RESPONSE, on_block_headers)
    #     self.nodes[0].p2p.send_protocol_msg(GetBlockHeaders(hashes=[block_hash]))
    #     handler.wait()

    def _test_stop(self):
        self.log.info("Test stop")
        try:
            self.nodes[0].stop()
            self.nodes[0].getpeerinfo()
            assert False
        except Exception:
            pass

    def get_nonce(self, sender, inc=True):
        if sender not in self.nonce_map:
            self.nonce_map[sender] = wait_for_initial_nonce_for_address(self.nodes[0], sender)
            # print("self.nonce_map[sender]:", self.nonce_map[sender] )
        else:
            self.nonce_map[sender] += 1
        return self.nonce_map[sender]
    
    def get_transaction(self):
        transaction = {
            # 'from': '0x1b981f81568edd843dcb5b407ff0dd2e25618622'.lower(),
            'to': 'cfxtest:aak7fsws4u4yf38fk870218p1h3gxut3ku00u1k1da',
            'nonce': 0,
            'value': 1,
            'gas': 100000,
            'gasPrice': 1,
            'storageLimit': 100,
            'epochHeight': 100,
            'chainId': 10
        }
        return transaction
 

if __name__ == "__main__":
    SignTest().main()
