// Copyright 2019 Conflux Foundation. All rights reserved.
// Conflux is free software and distributed under GNU General Public License.
// See http://www.gnu.org/licenses/

use crate::{executive_observer::ExecutiveObserver, substate::Substate};
use cfx_bytes::Bytes;
use cfx_types::{AddressWithSpace, U256};
use primitives::{
    receipt::{SortedStorageChanges, StorageChange},
    LogEntry, TransactionWithSignature,
};
use solidity_abi::{ABIDecodable, ABIDecodeError};
use typemap::ShareDebugMap;

use super::{
    fresh_executive::CostInfo,
    pre_checked_executive::{ExecutiveReturn, RefundInfo},
};

#[derive(Debug)]
pub struct Executed {
    /// Transaction base gas: 21000 (for tx) or 53000 (for contract creation) +
    /// calldata gas
    pub base_gas: u64,

    /// Gas used during execution of transaction.
    pub gas_used: U256,

    /// Fee that need to be paid by execution of this transaction.
    pub fee: U256,

    /// Gas charged during execution of transaction.
    pub gas_charged: U256,

    /// If the gas fee is born by designated sponsor.
    pub gas_sponsor_paid: bool,

    /// Vector of logs generated by transaction.
    pub logs: Vec<LogEntry>,

    /// If the storage cost is born by designated sponsor.
    pub storage_sponsor_paid: bool,

    /// Any accounts that occupy some storage.
    pub storage_collateralized: Vec<StorageChange>,

    /// Any accounts that release some storage.
    pub storage_released: Vec<StorageChange>,

    /// Addresses of contracts created during execution of transaction.
    /// Ordered from earliest creation.
    ///
    /// eg. sender creates contract A and A in constructor creates contract B
    ///
    /// B creation ends first, and it will be the first element of the vector.
    ///
    /// Note: if the contract init code return with empty output, the contract
    /// address is still included here, even if it is not considered as a
    /// contract. This is a strange behaviour from Parity's code and not become
    /// a part of the protocol.
    pub contracts_created: Vec<AddressWithSpace>,

    /// Transaction output.
    pub output: Bytes,

    /// Extension output of executed
    pub ext_result: ExecutedExt,
}

pub type ExecutedExt = ShareDebugMap;

impl Executed {
    pub(super) fn not_enough_balance_fee_charged(
        tx: &TransactionWithSignature, fee: &U256, cost: CostInfo,
        ext_result: ExecutedExt, spec: &Spec,
    ) -> Self
    {
        let gas_charged = if *tx.gas_price() == U256::zero() {
            U256::zero()
        } else {
            fee / tx.gas_price()
        };
        let mut gas_sponsor_paid = cost.gas_sponsored;
        let mut storage_sponsor_paid = cost.storage_sponsored;
        if !spec.cip78b {
            gas_sponsor_paid = false;
            storage_sponsor_paid = false;
        }
        Self {
            gas_used: *tx.gas(),
            gas_charged,
            fee: fee.clone(),
            gas_sponsor_paid,
            logs: vec![],
            contracts_created: vec![],
            storage_sponsor_paid,
            storage_collateralized: Vec::new(),
            storage_released: Vec::new(),
            output: Default::default(),
            base_gas: cost.base_gas,
            ext_result,
        }
    }

    pub(super) fn execution_error_fully_charged(
        tx: &TransactionWithSignature, cost: CostInfo, ext_result: ExecutedExt,
        spec: &Spec,
    ) -> Self
    {
        let mut storage_sponsor_paid = cost.storage_sponsored;
        let mut gas_sponsor_paid = cost.gas_sponsored;

        if !spec.cip78b {
            gas_sponsor_paid = false;
            storage_sponsor_paid = false;
        }
        Self {
            gas_used: *tx.gas(),
            gas_charged: *tx.gas(),
            fee: tx.gas().saturating_mul(*tx.gas_price()),
            gas_sponsor_paid,
            logs: vec![],
            contracts_created: vec![],
            storage_sponsor_paid,
            storage_collateralized: Vec::new(),
            storage_released: Vec::new(),
            output: Default::default(),
            base_gas: cost.base_gas,
            ext_result,
        }
    }

    pub(super) fn from_executive_return(
        r: &ExecutiveReturn, refund_info: RefundInfo, cost: CostInfo,
        substate: Substate, ext_result: ExecutedExt, spec: &Spec,
    ) -> Self
    {
        let output = r.return_data.to_vec();

        let SortedStorageChanges {
            storage_collateralized,
            storage_released,
        } = if r.apply_state {
            substate.compute_storage_changes()
        } else {
            Default::default()
        };

        let RefundInfo {
            gas_used,
            gas_charged,
            fees_value: fee,
            ..
        } = refund_info;
        let storage_sponsor_paid = if spec.cip78a {
            cost.storage_sponsored
        } else {
            cost.storage_sponsor_eligible
        };

        let gas_sponsor_paid = cost.gas_sponsored;

        Executed {
            gas_used,
            gas_charged,
            fee,
            gas_sponsor_paid,
            logs: substate.logs.to_vec(),
            contracts_created: substate.contracts_created.to_vec(),
            storage_sponsor_paid,
            storage_collateralized,
            storage_released,
            output,
            base_gas: cost.base_gas,
            ext_result,
        }
    }
}

pub fn make_ext_result<O: ExecutiveObserver>(observer: O) -> ShareDebugMap {
    let mut ext_result = ShareDebugMap::custom();
    observer.drain_trace(&mut ext_result);
    ext_result
}

pub fn revert_reason_decode(output: &Bytes) -> String {
    const MAX_LENGTH: usize = 50;
    let decode_result = if output.len() < 4 {
        Err(ABIDecodeError("Uncompleted Signature"))
    } else {
        let (sig, data) = output.split_at(4);
        if sig != [8, 195, 121, 160] {
            Err(ABIDecodeError("Unrecognized Signature"))
        } else {
            String::abi_decode(data)
        }
    };
    match decode_result {
        Ok(str) => {
            if str.len() < MAX_LENGTH {
                str
            } else {
                format!("{}...", str[..MAX_LENGTH].to_string())
            }
        }
        Err(_) => "".to_string(),
    }
}

use cfx_vm_types::Spec;

#[cfg(test)]
use rustc_hex::FromHex;

#[test]
fn test_decode_result() {
    let input_hex =
        "08c379a0\
         0000000000000000000000000000000000000000000000000000000000000020\
         0000000000000000000000000000000000000000000000000000000000000018\
         e699bae59586e4b88de8b6b3efbc8ce8afb7e58585e580bc0000000000000000";
    assert_eq!(
        "智商不足，请充值".to_string(),
        revert_reason_decode(&input_hex.from_hex().unwrap())
    );
}
