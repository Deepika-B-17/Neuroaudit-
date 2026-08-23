PRIVACY_DISCLAIMER = (
    "NeuroAudit estimates potential privacy exposure from neural data. Results are model-dependent "
    "and should not be interpreted as definitive statements about an individual's thoughts, emotions, "
    "identity, or medical condition."
)

def aggregate_privacy_risk(dimensions: list, features: dict, metadata: dict) -> dict:
    """
    Aggregate individual dimension risk scores into an overall Privacy Risk Score (0-100),
    assign risk levels, and generate customized executive summaries and key findings.
    """
    dim_map = {d["key"]: d for d in dimensions}
    id_score = dim_map.get("identity", {}).get("score", 50)
    em_score = dim_map.get("emotion", {}).get("score", 50)
    st_score = dim_map.get("stress", {}).get("score", 50)
    wl_score = dim_map.get("workload", {}).get("score", 50)

    # Calibrated weighting: Identity (30%), Emotion (25%), Stress (25%), Workload (20%)
    overall_risk = int(round(
        0.30 * id_score +
        0.25 * em_score +
        0.25 * st_score +
        0.20 * wl_score
    ))
    overall_risk = max(10, min(98, overall_risk))

    if overall_risk >= 70:
        risk_level = "HIGH"
    elif overall_risk >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Identify primary and secondary risk contributors
    sorted_dims = sorted(dimensions, key=lambda x: x["score"], reverse=True)
    top_dim = sorted_dims[0]
    second_dim = sorted_dims[1]

    # Generate Overall Summary
    overall_summary = (
        f"This neural privacy audit estimates {risk_level.lower()} overall privacy exposure ({overall_risk}/100), "
        f"driven primarily by {top_dim['label'].lower()}-related inference potential ({top_dim['score']}/100) "
        f"and {second_dim['label'].lower()}-related inference ({second_dim['score']}/100). "
        f"Scores describe estimated exposure under state-of-the-art neural decoding models."
    )

    # Generate Executive Summary
    executive_summary = (
        f"The analyzed EEG recording ({metadata.get('n_channels', 8)} channels, {metadata.get('duration_sec', 0)}s duration) "
        f"shows an overall privacy risk score of {overall_risk} / 100 ({risk_level.capitalize()}). "
        f"{top_dim['label']} inference represents the largest vector of sensitive disclosure ({top_dim['score']} / 100), "
        f"with {second_dim['label'].lower()} also showing {second_dim['level'].lower()} estimated exposure. "
        f"Protective measures such as differential privacy noise injection and cryptographic pseudonymization "
        f"are recommended to mitigate unintended participant profiling."
    )

    # Generate Key Findings
    key_findings = [
        f"{top_dim['label']}-related inference shows the highest estimated privacy exposure in this audit ({top_dim['score']} / 100).",
        f"{second_dim['label']}-related inference indicates {second_dim['level'].lower()} potential exposure based on signal spectral characteristics.",
        f"Frequency spectrum analysis reveals dominant {max(features.get('global_band_powers', {}), key=features.get('global_band_powers', {}).get, default='alpha')} band activity with an individual alpha peak at {features.get('iapf_hz', 10.0)} Hz.",
        f"Signal contains {metadata.get('n_channels', 8)} spatial channels across {metadata.get('duration_sec', 0)} seconds of continuous neural acquisition."
    ]

    return {
        "overallRisk": overall_risk,
        "riskLevel": risk_level,
        "overallSummary": overall_summary,
        "executiveSummary": executive_summary,
        "keyFindings": key_findings,
        "disclaimer": PRIVACY_DISCLAIMER
    }
