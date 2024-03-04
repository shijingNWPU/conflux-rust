#!/usr/bin/env python3
import datetime
import time
import os
import types
import shutil
from eth_utils import decode_hex

from conflux.messages import GetBlockHeaders, GET_BLOCK_HEADERS_RESPONSE
from test_framework.mininode import start_p2p_connection
from test_framework.test_framework import ConfluxTestFramework
from test_framework.util import assert_equal, connect_nodes, get_peer_addr, wait_until, WaitHandler, \
    initialize_datadir, PortMin, get_datadir_path, connect_sample_nodes, sync_blocks


class SignTest(ConfluxTestFramework):
    def set_test_params(self):
        self.num_nodes = 2
        self.conf_parameters = {
            "executive_trace": "true",
            "public_rpc_apis": "\"cfx,debug,test,pubsub,trace\"",
        }

    def setup_network(self):
        self.setup_nodes()

    def run_test(self):
        time.sleep(7)

        blocks = self.nodes[0].generate_empty_blocks(1)
        self.best_block_hash = blocks[-1] #make_genesis().block_header.hash

        self._test_quantum_sign()

        time.sleep(5)
        
        self._test_stop()

    def start_network(self, node_count):
        self.nodes = []
        self.add_nodes(node_count)
        for node_index in range(node_count):
            initialize_datadir(self.options.tmpdir, node_index, PortMin.n, self.conf_parameters)
            self.start_node(node_index, phase_to_wait=None)

        connect_sample_nodes(self.nodes, self.log, sample=self.num_nodes - 1)
        sync_blocks(self.nodes)
        for node in self.nodes:
            node.wait_for_recovery(["NormalSyncPhase"], 30)
            


    def _test_quantum_sign(self):
        module_name = "test_sign"
        module = __import__("rpc." + module_name, fromlist=True)
        
        obj_type = getattr(module, "TestSignTx") # RpcClient

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

        method_name = "test_quantum_sign"
        # method_name = "test_sign"
        method = getattr(obj, method_name)
        self.log.info("TestSignTx" + "." + method_name)
        method()



    def _test_addlatency(self):
        def on_block_headers(node, _):
            msec = (datetime.datetime.now() - node.start_time).total_seconds() * 1000
            self.log.info("Message arrived after " + str(msec) + "ms")
            # The EventLoop in rust may have a deviation of a maximum of
            # 100ms. This is because the ticker is 100ms by default.
            assert msec >= node.latency_ms - 100

        self.log.info("Test addlatency")
        block_hash = decode_hex(self.nodes[0].generate_empty_blocks(1)[0])
        default_node = start_p2p_connection([self.nodes[0]])[0]
        latency_ms = 1000
        self.nodes[0].addlatency(default_node.key, latency_ms)
        default_node.start_time = datetime.datetime.now()
        default_node.latency_ms = latency_ms
        handler = WaitHandler(default_node, GET_BLOCK_HEADERS_RESPONSE, on_block_headers)
        self.nodes[0].p2p.send_protocol_msg(GetBlockHeaders(hashes=[block_hash]))
        handler.wait()



    def _test_stop(self):
        self.log.info("Test stop")
        try:
            self.nodes[0].stop()
            self.nodes[0].getpeerinfo()
            assert False
        except Exception:
            pass

if __name__ == "__main__":
    SignTest().main()
