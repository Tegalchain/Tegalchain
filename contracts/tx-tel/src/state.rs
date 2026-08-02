use cosmwasm_schema::cw_serde;
use cosmwasm_std::{Addr, Decimal, Uint128};
use cw_storage_plus::{Item, Map};

#[cw_serde]
pub struct Config {
    pub admin: Addr,
    pub minter: Addr,
    pub min_eqs: Decimal,
    pub min_riv_exclusive: Decimal,
    pub min_consensus_confidence: Decimal,
    pub min_resonance_score: u64,
}

#[cw_serde]
pub struct MintRecord {
    pub gtr_id: String,
    pub gtr_hash: String,
    pub recipient: Addr,
    pub amount: Uint128,
    pub eqs: Decimal,
    pub riv: Decimal,
    pub consensus_confidence: Decimal,
    pub resonance_score: u64,
}

pub const CONFIG: Item<Config> = Item::new("config");
pub const TOTAL_SUPPLY: Item<Uint128> = Item::new("total_supply");
pub const BALANCES: Map<&Addr, Uint128> = Map::new("balances");
pub const MINTS_BY_GTR: Map<&str, MintRecord> = Map::new("mints_by_gtr");

pub const CONTRACT_NAME: &str = "crates.io:tx-tel";
pub const CONTRACT_VERSION: &str = env!("CARGO_PKG_VERSION");
pub const TOKEN_NAME: &str = "Telecom Transynth";
pub const TOKEN_SYMBOL: &str = "tXtel";
pub const TOKEN_DECIMALS: u8 = 0;
