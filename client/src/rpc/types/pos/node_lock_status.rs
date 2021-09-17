use cfx_types::U64;

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct NodeLockStatus {
    pub in_queue: Vec<VotePowerState>,
    pub locked: U64,
    pub out_queue: Vec<VotePowerState>,
    pub unlocked: U64,

    // Equals to the summation of in_queue + locked
    pub available_votes: U64,

    pub force_retired: bool,
    // If the staking is forfeited, the unlocked votes before forfeiting is
    // exempted.
    pub exempt_from_forfeit: Option<U64>,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct VotePowerState {
    pub start_block_number: U64,
    pub power: U64,
}
