use std::str::FromStr;

use cosmwasm_std::{
    to_json_binary, Binary, Decimal, Deps, DepsMut, Env, MessageInfo, Response, StdResult,
    Uint128,
};
use cw2::set_contract_version;

use crate::error::ContractError;
use crate::gates::check_eligibility;
use crate::msg::{
    BalanceResponse, ConfigResponse, EligibilityResponse, ExecuteMsg, InstantiateMsg,
    MintRecordResponse, QueryMsg, TokenInfoResponse, DEFAULT_MIN_CONSENSUS, DEFAULT_MIN_EQS,
    DEFAULT_MIN_RESONANCE,
};
use crate::state::{
    Config, MintRecord, BALANCES, CONFIG, CONTRACT_NAME, CONTRACT_VERSION, MINTS_BY_GTR,
    TOKEN_DECIMALS, TOKEN_NAME, TOKEN_SYMBOL, TOTAL_SUPPLY,
};

pub fn instantiate(
    deps: DepsMut,
    _env: Env,
    info: MessageInfo,
    msg: InstantiateMsg,
) -> Result<Response, ContractError> {
    let admin = match msg.admin {
        Some(a) => deps.api.addr_validate(&a)?,
        None => info.sender.clone(),
    };
    let minter = deps.api.addr_validate(&msg.minter)?;

    let min_eqs = msg
        .min_eqs
        .unwrap_or_else(|| Decimal::from_str(DEFAULT_MIN_EQS).unwrap());
    let min_riv_exclusive = msg.min_riv_exclusive.unwrap_or_else(Decimal::zero);
    let min_consensus_confidence = msg
        .min_consensus_confidence
        .unwrap_or_else(|| Decimal::from_str(DEFAULT_MIN_CONSENSUS).unwrap());
    let min_resonance_score = msg.min_resonance_score.unwrap_or(DEFAULT_MIN_RESONANCE);

    set_contract_version(deps.storage, CONTRACT_NAME, CONTRACT_VERSION)?;
    CONFIG.save(
        deps.storage,
        &Config {
            admin,
            minter: minter.clone(),
            min_eqs,
            min_riv_exclusive,
            min_consensus_confidence,
            min_resonance_score,
        },
    )?;
    TOTAL_SUPPLY.save(deps.storage, &Uint128::zero())?;

    Ok(Response::new()
        .add_attribute("action", "instantiate")
        .add_attribute("token", TOKEN_SYMBOL)
        .add_attribute("minter", minter))
}

pub fn execute(
    deps: DepsMut,
    _env: Env,
    info: MessageInfo,
    msg: ExecuteMsg,
) -> Result<Response, ContractError> {
    match msg {
        ExecuteMsg::Mint {
            recipient,
            gtr_id,
            gtr_hash,
            eqs,
            riv,
            consensus_confidence,
            resonance_score,
            amount,
        } => execute_mint(
            deps,
            info,
            recipient,
            gtr_id,
            gtr_hash,
            eqs,
            riv,
            consensus_confidence,
            resonance_score,
            amount,
        ),
        ExecuteMsg::UpdateMinter { minter } => execute_update_minter(deps, info, minter),
        ExecuteMsg::UpdateGates {
            min_eqs,
            min_riv_exclusive,
            min_consensus_confidence,
            min_resonance_score,
        } => execute_update_gates(
            deps,
            info,
            min_eqs,
            min_riv_exclusive,
            min_consensus_confidence,
            min_resonance_score,
        ),
        ExecuteMsg::TransferAdmin { admin } => execute_transfer_admin(deps, info, admin),
    }
}

fn execute_mint(
    deps: DepsMut,
    info: MessageInfo,
    recipient: String,
    gtr_id: String,
    gtr_hash: String,
    eqs: Decimal,
    riv: Decimal,
    consensus_confidence: Decimal,
    resonance_score: u64,
    amount: Option<Uint128>,
) -> Result<Response, ContractError> {
    let cfg = CONFIG.load(deps.storage)?;
    if info.sender != cfg.minter {
        return Err(ContractError::Unauthorized {});
    }
    if gtr_id.trim().is_empty() {
        return Err(ContractError::InvalidGtrId {});
    }
    if gtr_hash.trim().is_empty() || gtr_hash.len() < 16 {
        return Err(ContractError::InvalidGtrHash {});
    }

    let amount = amount.unwrap_or_else(Uint128::one);
    if amount.is_zero() {
        return Err(ContractError::InvalidAmount {});
    }

    if MINTS_BY_GTR
        .may_load(deps.storage, &gtr_id)?
        .is_some()
    {
        return Err(ContractError::AlreadyMinted { gtr_id });
    }

    let eligibility = check_eligibility(&cfg, eqs, riv, consensus_confidence, resonance_score);
    if !eligibility.eligible {
        return Err(ContractError::MintGateFailed {
            reason: eligibility.reasons.join("; "),
        });
    }

    let recipient = deps.api.addr_validate(&recipient)?;
    let balance = BALANCES
        .may_load(deps.storage, &recipient)?
        .unwrap_or_else(Uint128::zero);
    BALANCES.save(deps.storage, &recipient, &(balance + amount))?;

    let supply = TOTAL_SUPPLY.load(deps.storage)?;
    TOTAL_SUPPLY.save(deps.storage, &(supply + amount))?;

    MINTS_BY_GTR.save(
        deps.storage,
        &gtr_id,
        &MintRecord {
            gtr_id: gtr_id.clone(),
            gtr_hash: gtr_hash.clone(),
            recipient: recipient.clone(),
            amount,
            eqs,
            riv,
            consensus_confidence,
            resonance_score,
        },
    )?;

    Ok(Response::new()
        .add_attribute("action", "mint")
        .add_attribute("token", TOKEN_SYMBOL)
        .add_attribute("gtr_id", gtr_id)
        .add_attribute("gtr_hash", gtr_hash)
        .add_attribute("recipient", recipient)
        .add_attribute("amount", amount)
        .add_attribute("eqs", eqs.to_string())
        .add_attribute("riv", riv.to_string())
        .add_attribute("resonance_score", resonance_score.to_string()))
}

fn execute_update_minter(
    deps: DepsMut,
    info: MessageInfo,
    minter: String,
) -> Result<Response, ContractError> {
    let mut cfg = CONFIG.load(deps.storage)?;
    if info.sender != cfg.admin {
        return Err(ContractError::Unauthorized {});
    }
    cfg.minter = deps.api.addr_validate(&minter)?;
    CONFIG.save(deps.storage, &cfg)?;
    Ok(Response::new()
        .add_attribute("action", "update_minter")
        .add_attribute("minter", cfg.minter))
}

fn execute_update_gates(
    deps: DepsMut,
    info: MessageInfo,
    min_eqs: Option<Decimal>,
    min_riv_exclusive: Option<Decimal>,
    min_consensus_confidence: Option<Decimal>,
    min_resonance_score: Option<u64>,
) -> Result<Response, ContractError> {
    let mut cfg = CONFIG.load(deps.storage)?;
    if info.sender != cfg.admin {
        return Err(ContractError::Unauthorized {});
    }
    if let Some(v) = min_eqs {
        cfg.min_eqs = v;
    }
    if let Some(v) = min_riv_exclusive {
        cfg.min_riv_exclusive = v;
    }
    if let Some(v) = min_consensus_confidence {
        cfg.min_consensus_confidence = v;
    }
    if let Some(v) = min_resonance_score {
        cfg.min_resonance_score = v;
    }
    CONFIG.save(deps.storage, &cfg)?;
    Ok(Response::new().add_attribute("action", "update_gates"))
}

fn execute_transfer_admin(
    deps: DepsMut,
    info: MessageInfo,
    admin: String,
) -> Result<Response, ContractError> {
    let mut cfg = CONFIG.load(deps.storage)?;
    if info.sender != cfg.admin {
        return Err(ContractError::Unauthorized {});
    }
    cfg.admin = deps.api.addr_validate(&admin)?;
    CONFIG.save(deps.storage, &cfg)?;
    Ok(Response::new()
        .add_attribute("action", "transfer_admin")
        .add_attribute("admin", cfg.admin))
}

pub fn query(deps: Deps, _env: Env, msg: QueryMsg) -> StdResult<Binary> {
    match msg {
        QueryMsg::Config {} => to_json_binary(&query_config(deps)?),
        QueryMsg::TokenInfo {} => to_json_binary(&query_token_info(deps)?),
        QueryMsg::Balance { address } => to_json_binary(&query_balance(deps, address)?),
        QueryMsg::MintRecord { gtr_id } => to_json_binary(&query_mint_record(deps, gtr_id)?),
        QueryMsg::CheckEligibility {
            eqs,
            riv,
            consensus_confidence,
            resonance_score,
        } => to_json_binary(&query_eligibility(
            deps,
            eqs,
            riv,
            consensus_confidence,
            resonance_score,
        )?),
    }
}

fn query_config(deps: Deps) -> StdResult<ConfigResponse> {
    let cfg = CONFIG.load(deps.storage)?;
    let total_supply = TOTAL_SUPPLY.load(deps.storage)?;
    Ok(ConfigResponse {
        admin: cfg.admin.to_string(),
        minter: cfg.minter.to_string(),
        min_eqs: cfg.min_eqs,
        min_riv_exclusive: cfg.min_riv_exclusive,
        min_consensus_confidence: cfg.min_consensus_confidence,
        min_resonance_score: cfg.min_resonance_score,
        total_supply,
    })
}

fn query_token_info(deps: Deps) -> StdResult<TokenInfoResponse> {
    let total_supply = TOTAL_SUPPLY.load(deps.storage)?;
    Ok(TokenInfoResponse {
        name: TOKEN_NAME.to_string(),
        symbol: TOKEN_SYMBOL.to_string(),
        decimals: TOKEN_DECIMALS,
        total_supply,
    })
}

fn query_balance(deps: Deps, address: String) -> StdResult<BalanceResponse> {
    let addr = deps.api.addr_validate(&address)?;
    let balance = BALANCES
        .may_load(deps.storage, &addr)?
        .unwrap_or_else(Uint128::zero);
    Ok(BalanceResponse { balance })
}

fn query_mint_record(deps: Deps, gtr_id: String) -> StdResult<MintRecordResponse> {
    match MINTS_BY_GTR.may_load(deps.storage, &gtr_id)? {
        Some(r) => Ok(MintRecordResponse {
            found: true,
            gtr_id: r.gtr_id,
            gtr_hash: Some(r.gtr_hash),
            recipient: Some(r.recipient.to_string()),
            amount: Some(r.amount),
            eqs: Some(r.eqs),
            riv: Some(r.riv),
            consensus_confidence: Some(r.consensus_confidence),
            resonance_score: Some(r.resonance_score),
        }),
        None => Ok(MintRecordResponse {
            found: false,
            gtr_id,
            gtr_hash: None,
            recipient: None,
            amount: None,
            eqs: None,
            riv: None,
            consensus_confidence: None,
            resonance_score: None,
        }),
    }
}

fn query_eligibility(
    deps: Deps,
    eqs: Decimal,
    riv: Decimal,
    consensus_confidence: Decimal,
    resonance_score: u64,
) -> StdResult<EligibilityResponse> {
    let cfg = CONFIG.load(deps.storage)?;
    Ok(check_eligibility(
        &cfg,
        eqs,
        riv,
        consensus_confidence,
        resonance_score,
    ))
}
