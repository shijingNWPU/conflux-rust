// Copyright 2020 Conflux Foundation. All rights reserved.
// Conflux is free software and distributed under GNU General Public License.
// See http://www.gnu.org/licenses/

use cfx_parameters::internal_contract_addresses::ADMIN_CONTROL_CONTRACT_ADDRESS;
use cfx_types::{Address, U256};
use primitives::BlockNumber;

use super::{super::impls::admin::*, preludes::*};

make_solidity_contract! {
    pub struct AdminControl(ADMIN_CONTROL_CONTRACT_ADDRESS, generate_fn_table, "active_at_genesis");
}
fn generate_fn_table() -> SolFnTable {
    make_function_table!(SetAdmin, Destroy, GetAdmin)
}
group_impl_is_active!("genesis", SetAdmin, Destroy, GetAdmin);

make_solidity_function! {
    struct SetAdmin((Address, Address), "setAdmin(address,address)");
}
impl_function_type!(SetAdmin, "non_payable_write", gas: |spec: &Spec| spec.sstore_reset_gas);

impl SimpleExecutionTrait for SetAdmin {
    fn execute_inner(
        &self, inputs: (Address, Address), params: &ActionParams,
        context: &mut InternalRefContext,
    ) -> vm::Result<()> {
        set_admin(inputs.0, inputs.1, params, context)
    }
}

make_solidity_function! {
    struct Destroy(Address, "destroy(address)");
}
impl_function_type!(Destroy, "non_payable_write", gas: |spec: &Spec| spec.sstore_reset_gas);

impl SimpleExecutionTrait for Destroy {
    fn execute_inner(
        &self, input: Address, params: &ActionParams,
        context: &mut InternalRefContext,
    ) -> vm::Result<()> {
        destroy(
            input,
            params,
            context.state,
            context.spec,
            context.substate,
            context.tracer,
        )
    }
}

make_solidity_function! {
    struct GetAdmin(Address, "getAdmin(address)", Address);
}
impl_function_type!(GetAdmin, "query_with_default_gas");

impl SimpleExecutionTrait for GetAdmin {
    fn execute_inner(
        &self, input: Address, _params: &ActionParams,
        context: &mut InternalRefContext,
    ) -> vm::Result<Address> {
        Ok(context.state.admin(&input)?)
    }
}

#[test]
fn test_admin_contract_sig_v2() {
    // Check the consistency between signature generated by rust code and java
    // sdk.
    check_func_signature!(GetAdmin, "64efb22b");
    check_func_signature!(SetAdmin, "c55b6bb7");
    check_func_signature!(Destroy, "00f55d9d");
}
