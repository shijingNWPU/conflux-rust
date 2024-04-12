import time

import eth_utils
import rlp
import sys

from conflux.config import default_config

sys.path.append("..")

from conflux.address import hex_to_b32_address
from conflux.rpc import RpcClient
from test_framework.util import assert_equal, assert_raises_rpc_error, assert_is_hash_string

sys.path.append("../../../cfx-account")
from cfx_account._utils.transactions import serializable_unsigned_transaction_from_dict

import binascii

from cfx_account.account import (
    Account
)

key = '0x46b9e861b63d3509c88b7817275a30d22d62c8cd8fa6486ddee35ef0d8e0495f'

class TestSignTx(RpcClient):
    def test_quantum_sign(self, transaction, addrssss):
        # 一个账户转账
        start_sign_time = time.perf_counter_ns()
        signed_tx = Account.sign_transaction_post_quantum(transaction, key)
        print("【performance】sign:", time.perf_counter_ns() - start_sign_time )

        file = open("file.txt", "a")
        file.write("\n【performance】sign:"+ str(time.perf_counter_ns() - start_sign_time ))
        file.close()

        # print("signed_tx:", signed_tx)
        
        # print(signed_tx.rawTransaction.hex())
        print("-----------------------\nbefore: self.check_tx_in_pool():", self.check_tx_in_pool())

        print("signed_tx.rawTransaction.hex():", signed_tx.rawTransaction.hex())

        self.send_raw_tx( signed_tx.rawTransaction.hex() )

        # assert_raises_rpc_error(None, None, self.send_raw_tx, signed_tx.rawTransaction.hex())

        print("-----------------------\nafter: self.check_tx_in_pool():", self.check_tx_in_pool())

        # while True:
        #     user_input = input("enter 'q' to exit:")
        #     if user_input == 'q':
        #         break
        time.sleep(15)

    def test_sign(self, transaction, addrssss):
        account = Account.from_key(key)

        start_sign_time = time.perf_counter_ns()
        
        signed_tx = Account.sign_transaction_elliptic_curve(transaction, key)
        
        file = open("file.txt", "a")
        file.write("\n【performance】sign:"+ str(time.perf_counter_ns() - start_sign_time ))
        file.close()

        print("【performance】sign:", time.perf_counter_ns() - start_sign_time )
        print("-----------------------\nbefore: self.check_tx_in_pool():", self.check_tx_in_pool())
        print("signed_tx.rawTransaction.hex():", signed_tx.rawTransaction.hex())
    
        self.send_raw_tx( signed_tx.rawTransaction.hex() )

        # assert_raises_rpc_error(None, None, self.send_raw_tx, signed_tx.rawTransaction.hex())

        print("-----------------------\nafter: self.check_tx_in_pool():", self.check_tx_in_pool())


        # while True:
        #     user_input = input("enter 'q' to exit:")
        #     if user_input == 'q':
        #         break
        time.sleep(5)

    def get_sign_address(self):
        account = Account.from_key(key)
        return account.address

    def get_quantum_address(self):
        address = "0x148c7dca248da87500367be3ca2d70dbd90bf97c"
        return address



class TestPool(RpcClient):
    def test_sign_tx_in_pool(self):
        print("-----------------------\nself.check_tx_in_pool():", self.check_tx_in_pool())


