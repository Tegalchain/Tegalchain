use cosmwasm_std::testing::{mock_dependencies, mock_env, mock_info};
use cosmwasm_std::{from_json, Addr, Decimal, Uint128};
use std::str::FromStr;

use crate::contract::{execute, instantiate, query};
use crate::error::ContractError;
use crate::msg::{
    BalanceResponse, ConfigResponse, EligibilityResponse, ExecuteMsg, InstantiateMsg,
    MintRecordResponse, QueryMsg, TokenInfoResponse,
};

fn d(s: &str) -> Decimal {
    Decimal::from_str(s).unwrap()
}

fn setup() -> (cosmwasm_std::OwnedDeps<
    cosmwasm_std::MemoryStorage,
    cosmwasm_std::testing::MockApi,
    cosmwasm_std::testing::MockQuerier,
>, Addr) {
    let mut deps = mock_dependencies();
    let info = mock_info("admin", &[]);
    let msg = InstantiateMsg {
        admin: None,
        minter: "oracle".to_string(),
        min_eqs: None,
        min_riv_exclusive: None,
        min_consensus_confidence: None,
        min_resonance_score: None,
    };
    instantiate(deps.as_mut(), mock_env(), info, msg).unwrap();
    (deps, Addr::unchecked("oracle"))
}

#[test]
fn instantiate_sets_lab_gates() {
    let (deps, _) = setup();
    let bin = query(deps.as_ref(), mock_env(), QueryMsg::Config {}).unwrap();
    let cfg: ConfigResponse = from_json(bin).unwrap();
    assert_eq!(cfg.minter, "oracle");
    assert_eq!(cfg.min_eqs, d("0.7"));
    assert_eq!(cfg.min_riv_exclusive, Decimal::zero());
    assert_eq!(cfg.min_consensus_confidence, d("1"));
    assert_eq!(cfg.min_resonance_score, 50);
    assert_eq!(cfg.total_supply, Uint128::zero());

    let bin = query(deps.as_ref(), mock_env(), QueryMsg::TokenInfo {}).unwrap();
    let token: TokenInfoResponse = from_json(bin).unwrap();
    assert_eq!(token.symbol, "tXtel");
}

#[test]
fn mint_succeeds_when_gates_pass() {
    let (mut deps, _) = setup();
    let info = mock_info("oracle", &[]);
    let msg = ExecuteMsg::Mint {
        recipient: "zeegate".to_string(),
        gtr_id: "gtr-001".to_string(),
        gtr_hash: "a".repeat(64),
        eqs: d("0.75"),
        riv: d("12.5"),
        consensus_confidence: d("1"),
        resonance_score: 62,
        amount: None,
    };
    let res = execute(deps.as_mut(), mock_env(), info, msg).unwrap();
    assert!(res.attributes.iter().any(|a| a.key == "action" && a.value == "mint"));

    let bin = query(
        deps.as_ref(),
        mock_env(),
        QueryMsg::Balance {
            address: "zeegate".to_string(),
        },
    )
    .unwrap();
    let bal: BalanceResponse = from_json(bin).unwrap();
    assert_eq!(bal.balance, Uint128::one());

    let bin = query(
        deps.as_ref(),
        mock_env(),
        QueryMsg::MintRecord {
            gtr_id: "gtr-001".to_string(),
        },
    )
    .unwrap();
    let rec: MintRecordResponse = from_json(bin).unwrap();
    assert!(rec.found);
    assert_eq!(rec.amount, Some(Uint128::one()));
}

#[test]
fn mint_rejects_low_eqs() {
    let (mut deps, _) = setup();
    let info = mock_info("oracle", &[]);
    let err = execute(
        deps.as_mut(),
        mock_env(),
        info,
        ExecuteMsg::Mint {
            recipient: "zeegate".to_string(),
            gtr_id: "gtr-low".to_string(),
            gtr_hash: "b".repeat(64),
            eqs: d("0.69"),
            riv: d("1"),
            consensus_confidence: d("1"),
            resonance_score: 50,
            amount: None,
        },
    )
    .unwrap_err();
    match err {
        ContractError::MintGateFailed { reason } => {
            assert!(reason.contains("eqs"));
        }
        other => panic!("unexpected error: {other:?}"),
    }
}

#[test]
fn mint_rejects_zero_riv() {
    let (mut deps, _) = setup();
    let err = execute(
        deps.as_mut(),
        mock_env(),
        mock_info("oracle", &[]),
        ExecuteMsg::Mint {
            recipient: "zeegate".to_string(),
            gtr_id: "gtr-riv".to_string(),
            gtr_hash: "c".repeat(64),
            eqs: d("0.9"),
            riv: Decimal::zero(),
            consensus_confidence: d("1"),
            resonance_score: 80,
            amount: None,
        },
    )
    .unwrap_err();
    assert!(matches!(err, ContractError::MintGateFailed { .. }));
}

#[test]
fn mint_rejects_non_minter() {
    let (mut deps, _) = setup();
    let err = execute(
        deps.as_mut(),
        mock_env(),
        mock_info("alice", &[]),
        ExecuteMsg::Mint {
            recipient: "zeegate".to_string(),
            gtr_id: "gtr-x".to_string(),
            gtr_hash: "d".repeat(64),
            eqs: d("0.9"),
            riv: d("1"),
            consensus_confidence: d("1"),
            resonance_score: 80,
            amount: None,
        },
    )
    .unwrap_err();
    assert_eq!(err, ContractError::Unauthorized {});
}

#[test]
fn mint_rejects_duplicate_gtr() {
    let (mut deps, _) = setup();
    let mint = ExecuteMsg::Mint {
        recipient: "zeegate".to_string(),
        gtr_id: "gtr-dup".to_string(),
        gtr_hash: "e".repeat(64),
        eqs: d("0.8"),
        riv: d("2"),
        consensus_confidence: d("1"),
        resonance_score: 55,
        amount: Some(Uint128::new(3)),
    };
    execute(deps.as_mut(), mock_env(), mock_info("oracle", &[]), mint.clone()).unwrap();
    let err = execute(deps.as_mut(), mock_env(), mock_info("oracle", &[]), mint).unwrap_err();
    assert!(matches!(err, ContractError::AlreadyMinted { .. }));
}

#[test]
fn check_eligibility_query() {
    let (deps, _) = setup();
    let bin = query(
        deps.as_ref(),
        mock_env(),
        QueryMsg::CheckEligibility {
            eqs: d("0.7"),
            riv: d("0.01"),
            consensus_confidence: d("1"),
            resonance_score: 50,
        },
    )
    .unwrap();
    let resp: EligibilityResponse = from_json(bin).unwrap();
    assert!(resp.eligible);
    assert!(resp.reasons.is_empty());
}
