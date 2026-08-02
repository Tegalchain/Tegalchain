use cosmwasm_std::StdError;
use thiserror::Error;

#[derive(Error, Debug, PartialEq)]
pub enum ContractError {
    #[error("{0}")]
    Std(#[from] StdError),

    #[error("unauthorized")]
    Unauthorized {},

    #[error("gtr_id already minted: {gtr_id}")]
    AlreadyMinted { gtr_id: String },

    #[error("mint gate failed: {reason}")]
    MintGateFailed { reason: String },

    #[error("invalid mint amount")]
    InvalidAmount {},

    #[error("invalid gtr_id")]
    InvalidGtrId {},

    #[error("invalid gtr_hash")]
    InvalidGtrHash {},
}
