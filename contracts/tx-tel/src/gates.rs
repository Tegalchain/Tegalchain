use cosmwasm_std::Decimal;

use crate::msg::EligibilityResponse;
use crate::state::Config;

/// Evaluate PoREX lab mint gates against RFM fields.
pub fn check_eligibility(
    cfg: &Config,
    eqs: Decimal,
    riv: Decimal,
    consensus_confidence: Decimal,
    resonance_score: u64,
) -> EligibilityResponse {
    let mut reasons = Vec::new();

    if eqs < cfg.min_eqs {
        reasons.push(format!(
            "eqs {} < min_eqs {}",
            eqs, cfg.min_eqs
        ));
    }
    if riv <= cfg.min_riv_exclusive {
        reasons.push(format!(
            "riv {} must be > {}",
            riv, cfg.min_riv_exclusive
        ));
    }
    if consensus_confidence < cfg.min_consensus_confidence {
        reasons.push(format!(
            "consensus_confidence {} < min {}",
            consensus_confidence, cfg.min_consensus_confidence
        ));
    }
    if resonance_score < cfg.min_resonance_score {
        reasons.push(format!(
            "resonance_score {} < min {}",
            resonance_score, cfg.min_resonance_score
        ));
    }

    EligibilityResponse {
        eligible: reasons.is_empty(),
        reasons,
    }
}
