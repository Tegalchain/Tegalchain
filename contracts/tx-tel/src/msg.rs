use cosmwasm_schema::{cw_serde, QueryResponses};
use cosmwasm_std::{Decimal, Uint128};

/// Lab defaults from TP-102 PoREX mint gates (Phase 1).
pub const DEFAULT_MIN_EQS: &str = "0.70";
pub const DEFAULT_MIN_CONSENSUS: &str = "1.0";
pub const DEFAULT_MIN_RESONANCE: u64 = 50;

#[cw_serde]
pub struct InstantiateMsg {
    /// Optional admin (defaults to instantiator). Can update minter/gates.
    pub admin: Option<String>,
    /// Oracle / mint-worker address authorized to call Mint.
    pub minter: String,
    /// Minimum EQS (default 0.70).
    pub min_eqs: Option<Decimal>,
    /// RIV must be strictly greater than this (default 0).
    pub min_riv_exclusive: Option<Decimal>,
    /// Minimum consensus confidence (default 1.0 for oracle profile).
    pub min_consensus_confidence: Option<Decimal>,
    /// Minimum evidence resonance score (default 50).
    pub min_resonance_score: Option<u64>,
}

#[cw_serde]
pub enum ExecuteMsg {
    /// Mint tXtel when GLE/PoRE RFM fields pass gates. One mint per gtr_id.
    Mint {
        recipient: String,
        gtr_id: String,
        /// Content / GTR hash (SHA-256 hex of canonical TP-101 JSON).
        gtr_hash: String,
        eqs: Decimal,
        riv: Decimal,
        consensus_confidence: Decimal,
        resonance_score: u64,
        /// Amount of tXtel base units (default 1).
        amount: Option<Uint128>,
    },
    /// Admin: rotate oracle minter.
    UpdateMinter { minter: String },
    /// Admin: update PoREX gates.
    UpdateGates {
        min_eqs: Option<Decimal>,
        min_riv_exclusive: Option<Decimal>,
        min_consensus_confidence: Option<Decimal>,
        min_resonance_score: Option<u64>,
    },
    /// Admin: transfer admin rights.
    TransferAdmin { admin: String },
}

#[cw_serde]
#[derive(QueryResponses)]
pub enum QueryMsg {
    #[returns(ConfigResponse)]
    Config {},
    #[returns(TokenInfoResponse)]
    TokenInfo {},
    #[returns(BalanceResponse)]
    Balance { address: String },
    #[returns(MintRecordResponse)]
    MintRecord { gtr_id: String },
    #[returns(EligibilityResponse)]
    CheckEligibility {
        eqs: Decimal,
        riv: Decimal,
        consensus_confidence: Decimal,
        resonance_score: u64,
    },
}

#[cw_serde]
pub struct ConfigResponse {
    pub admin: String,
    pub minter: String,
    pub min_eqs: Decimal,
    pub min_riv_exclusive: Decimal,
    pub min_consensus_confidence: Decimal,
    pub min_resonance_score: u64,
    pub total_supply: Uint128,
}

#[cw_serde]
pub struct TokenInfoResponse {
    pub name: String,
    pub symbol: String,
    pub decimals: u8,
    pub total_supply: Uint128,
}

#[cw_serde]
pub struct BalanceResponse {
    pub balance: Uint128,
}

#[cw_serde]
pub struct MintRecordResponse {
    pub found: bool,
    pub gtr_id: String,
    pub gtr_hash: Option<String>,
    pub recipient: Option<String>,
    pub amount: Option<Uint128>,
    pub eqs: Option<Decimal>,
    pub riv: Option<Decimal>,
    pub consensus_confidence: Option<Decimal>,
    pub resonance_score: Option<u64>,
}

#[cw_serde]
pub struct EligibilityResponse {
    pub eligible: bool,
    pub reasons: Vec<String>,
}
