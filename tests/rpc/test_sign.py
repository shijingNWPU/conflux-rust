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
    def test_quantum_sign(self):
        account = Account.from_key(key)
        transaction = {
            # 'from': '0x1b981f81568edd843dcb5b407ff0dd2e25618622'.lower(),
            'to': 'cfxtest:aak7fsws4u4yf38fk870218p1h3gxut3ku00u1k1da',
            'nonce': 1,
            'value': 1,
            'gas': 100000,
            'gasPrice': 1,
            'storageLimit': 100,
            'epochHeight': 100,
            'chainId': 10
        }
        signed_tx = Account.sign_transaction_post_quantum(transaction, key)

        # print("signed_tx:", signed_tx)
        
        # print(signed_tx.rawTransaction.hex())
        print("-----------------------\nself.check_tx_in_pool():", self.check_tx_in_pool())

        print("signed_tx.rawTransaction.hex():", signed_tx.rawTransaction.hex())

        self.send_raw_tx( signed_tx.rawTransaction.hex() )

        # assert_raises_rpc_error(None, None, self.send_raw_tx, signed_tx.rawTransaction.hex())

        print("-----------------------\nself.check_tx_in_pool():", self.check_tx_in_pool())

        while True:
            user_input = input("enter 'q' to exit:")
            if user_input == 'q':
                break

    def test_sign(self):
        account = Account.from_key(key)
        transaction = {
            # 'from': '0x1b981f81568edd843dcb5b407ff0dd2e25618622'.lower(),
            'to': 'cfxtest:aak7fsws4u4yf38fk870218p1h3gxut3ku00u1k1da',
            'nonce': 1,
            'value': 1,
            'gas': 100000,
            'gasPrice': 1,
            'storageLimit': 100,
            'epochHeight': 100,
            'chainId': 10
        }
        signed_tx = Account.sign_transaction_elliptic_curve(transaction, key)

        print("-----------------------\nself.check_tx_in_pool():", self.check_tx_in_pool())

        print("signed_tx.rawTransaction.hex():", signed_tx.rawTransaction.hex())

        self.send_raw_tx( signed_tx.rawTransaction.hex() )

        # assert_raises_rpc_error(None, None, self.send_raw_tx, signed_tx.rawTransaction.hex())

        print("-----------------------\nself.check_tx_in_pool():", self.check_tx_in_pool())


        while True:
            user_input = input("enter 'q' to exit:")
            if user_input == 'q':
                break

    def test_encode_invalid_hex(self):
        # empty
        assert_raises_rpc_error(None, None, self.send_raw_tx, "")
        assert_raises_rpc_error(None, None, self.send_raw_tx, "0x")
        # odd length
        assert_raises_rpc_error(None, None, self.send_raw_tx, "0x123")
        # invalid character
        assert_raises_rpc_error(None, None, self.send_raw_tx, "0x123G")

    def test_encode_invalid_rlp(self):
        tx = self.new_tx()
        encoded = eth_utils.encode_hex(rlp.encode(tx))

        assert_raises_rpc_error(None, None, self.send_raw_tx, encoded + "12")  # 1 more byte
        assert_raises_rpc_error(None, None, self.send_raw_tx, encoded[0:-2])  # 1 less byte

    def test_address_prefix(self):
        # call builtin address starts with 0x0
        tx = self.new_tx(receiver="0x0000000000000000000000000000000000000002", data=b'\x00' * 32, gas=21128)
        assert_equal(self.send_tx(tx, True), tx.hash_hex())
        # non-builtin address starts with 0x0
        tx = self.new_tx(receiver="0x00e45681ac6c53d5a40475f7526bac1fe7590fb8")
        assert_equal(self.send_tx(tx, True), tx.hash_hex())
        # call address starts with 0x30
        tx = self.new_tx(receiver="0x30e45681ac6c53d5a40475f7526bac1fe7590fb8")
        encoded = eth_utils.encode_hex(rlp.encode(tx))
        assert_raises_rpc_error(None, None, self.send_raw_tx, encoded)
        # call address starts with 0x10
        tx = self.new_tx(receiver="0x10e45681ac6c53d5a40475f7526bac1fe7590fb8")
        assert_equal(self.send_tx(tx, True), tx.hash_hex())

    def test_signature_empty(self):
        tx = self.new_tx(sign=False)
        assert_raises_rpc_error(None, None, self.send_tx, tx)
