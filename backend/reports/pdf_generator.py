"""
NeuroAudit Phase 2 — PDF Report Generator

Uses ReportLab to produce a publication-grade PDF audit report containing:
  1.  NeuroAudit branding & header
  2.  Audit metadata grid
  3.  Overall Privacy Risk Score + risk level
  4.  Executive Summary
  5.  EEG Quality Report
  6.  Dimension Risk Breakdown table
  7.  Per-dimension evidence, threat, and contributing indicators
  8.  Key Privacy Exposure Findings
  9.  Prioritised Security Recommendations
      - evidence, threat scenario, implementation steps
      - expected impact, residual risk, evidence status
  10. Limitations & Disclaimer

Scientific language policy
--------------------------
The report uses hedged language throughout:
  "the heuristic baseline indicates …"
  "is expected to reduce …"
  "should be evaluated for reduction"
Never: "proves", "confirms", "guarantees", "reduces risk by X%"
unless experimentally validated.
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
C_DARK     = colors.HexColor("#0F172A")   # slate-900
C_MUTED    = colors.HexColor("#64748B")   # slate-500
C_ACCENT   = colors.HexColor("#0284C7")   # sky-600
C_BORDER   = colors.HexColor("#CBD5E1")   # slate-300
C_BG       = colors.HexColor("#F8FAFC")   # slate-50
C_HIGH_FG  = colors.HexColor("#EF4444")   # red-500
C_HIGH_BG  = colors.HexColor("#FEE2E2")   # red-100
C_MED_FG   = colors.HexColor("#D97706")   # amber-600
C_MED_BG   = colors.HexColor("#FEF3C7")   # amber-100
C_LOW_FG   = colors.HexColor("#059669")   # emerald-600
C_LOW_BG   = colors.HexColor("#D1FAE5")   # emerald-100
C_CRITICAL = colors.HexColor("#7C3AED")   # violet-700


def _risk_colors(level: str):
    lvl = (level or "").upper()
    if lvl == "HIGH":     return C_HIGH_FG, C_HIGH_BG
    if lvl == "MEDIUM":   return C_MED_FG,  C_MED_BG
    return C_LOW_FG, C_LOW_BG


def _priority_color(priority: str):
    p = (priority or "").upper()
    if p == "CRITICAL": return C_CRITICAL
    if p == "HIGH":     return C_HIGH_FG
    if p == "MEDIUM":   return C_MED_FG
    return C_LOW_FG


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------

def _styles():
    base = getSampleStyleSheet()

    def mk(name, **kw):
        parent = kw.pop("parent", base["Normal"])
        return ParagraphStyle(name, parent=parent, **kw)

    return {
        "title":    mk("DocTitle",    fontName="Helvetica-Bold",  fontSize=22, leading=26, textColor=C_DARK),
        "subtitle": mk("DocSub",      fontName="Helvetica-Bold",  fontSize=8,  leading=10, textColor=C_ACCENT, spaceAfter=10),
        "sec":      mk("SecHead",     fontName="Helvetica-Bold",  fontSize=9,  leading=12, textColor=C_MUTED,  spaceBefore=10, spaceAfter=5),
        "subsec":   mk("SubSecHead",  fontName="Helvetica-Bold",  fontSize=8,  leading=11, textColor=C_DARK,   spaceBefore=6,  spaceAfter=3),
        "body":     mk("BodyDark",    fontName="Helvetica",       fontSize=8.5,leading=12, textColor=C_DARK),
        "muted":    mk("BodyMuted",   fontName="Helvetica",       fontSize=8,  leading=11, textColor=C_MUTED),
        "score":    mk("BigScore",    fontName="Helvetica-Bold",  fontSize=28, leading=32, textColor=C_DARK),
        "label":    mk("FieldLabel",  fontName="Helvetica-Bold",  fontSize=7.5,leading=10, textColor=C_MUTED),
        "badge":    mk("Badge",       fontName="Helvetica-Bold",  fontSize=8,  leading=10, textColor=C_DARK),
        "bullet":   mk("Bullet",      fontName="Helvetica",       fontSize=8,  leading=12, textColor=C_DARK, leftIndent=8),
    }


def _hr(story, thickness=1.0):
    story.append(HRFlowable(width="100%", thickness=thickness, color=C_BORDER, spaceBefore=6, spaceAfter=6))


def _sp(story, h=6):
    story.append(Spacer(1, h))


# ---------------------------------------------------------------------------
# Main report builder
# ---------------------------------------------------------------------------

def generate_pdf_report(audit: dict) -> bytes:
    """
    Build and return a complete PDF audit report as raw bytes.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=40, rightMargin=40,
        topMargin=38,  bottomMargin=38,
    )
    S   = _styles()
    story = []

    # ------------------------------------------------------------------ #
    # 1. Header
    # ------------------------------------------------------------------ #
    story.append(Paragraph("<b>NEUROAUDIT</b>", S["title"]))
    story.append(Paragraph("NEURAL DATA PRIVACY RISK ASSESSMENT REPORT — PHASE 2 HEURISTIC BASELINE", S["subtitle"]))
    _hr(story)

    # ------------------------------------------------------------------ #
    # 2. Metadata grid
    # ------------------------------------------------------------------ #
    date_val   = audit.get("analysisDate", datetime.utcnow().strftime("%d %b %Y"))
    status_val = audit.get("status", "Complete")
    sid        = audit.get("session_id", "N/A")

    meta_rows = [
        [
            Paragraph("<b>Audit Name:</b>", S["label"]),
            Paragraph(str(audit.get("auditName", "N/A")), S["body"]),
            Paragraph("<b>Analysis Date:</b>", S["label"]),
            Paragraph(date_val, S["body"]),
        ],
        [
            Paragraph("<b>EEG File:</b>", S["label"]),
            Paragraph(str(audit.get("fileName", "recording.edf")), S["body"]),
            Paragraph("<b>Session ID:</b>", S["label"]),
            Paragraph(sid, S["muted"]),
        ],
        [
            Paragraph("<b>Status:</b>", S["label"]),
            Paragraph(f"<font color='#059669'><b>{status_val}</b></font>", S["body"]),
            Paragraph("<b>Phase:</b>", S["label"]),
            Paragraph("Phase 2 — Heuristic Baseline", S["muted"]),
        ],
    ]
    meta_tbl = Table(meta_rows, colWidths=[80, 185, 90, 185])
    meta_tbl.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("TOPPADDING",    (0,0), (-1,-1), 2),
    ]))
    story.append(meta_tbl)
    _hr(story)

    # ------------------------------------------------------------------ #
    # 3. Overall Risk Score + Executive Summary
    # ------------------------------------------------------------------ #
    overall_risk = audit.get("overallRisk", 50)
    risk_level   = audit.get("riskLevel",  "MEDIUM").upper()
    fg, _        = _risk_colors(risk_level)
    exec_txt     = audit.get("executiveSummary", audit.get("overallSummary", ""))

    score_cell = [
        Paragraph(
            f"{overall_risk} <font size=13 color='#64748B'>/ 100</font>",
            S["score"],
        ),
        Paragraph(
            f"<font color='{fg.hexval()}'><b>{risk_level} PRIVACY RISK</b></font>",
            S["subtitle"],
        ),
    ]
    summary_cell = [
        Paragraph("<b>EXECUTIVE SUMMARY</b>", S["sec"]),
        Paragraph(exec_txt, S["body"]),
    ]
    exec_tbl = Table([[score_cell, summary_cell]], colWidths=[140, 400])
    exec_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_BG),
        ("BOX",        (0,0), (-1,-1), 1, C_BORDER),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1),8),
        ("LEFTPADDING",(0,0),(-1,-1), 10),
        ("RIGHTPADDING",(0,0),(-1,-1),10),
    ]))
    story.append(exec_tbl)
    _sp(story, 10)

    # ------------------------------------------------------------------ #
    # 4. EEG Quality Report
    # ------------------------------------------------------------------ #
    qr = audit.get("qualityReport", {})
    if qr:
        story.append(Paragraph("<b>EEG SIGNAL QUALITY REPORT</b>", S["sec"]))
        q_passed = qr.get("passed", True)
        q_suf    = qr.get("sufficient_for_assessment", True)
        q_flags  = qr.get("flags", [])
        q_warns  = qr.get("warnings", [])
        q_det    = qr.get("details", {})

        q_status_color = "#059669" if q_passed else "#EF4444"
        q_status_txt   = "PASSED" if q_passed else "ISSUES DETECTED"
        q_rows = [
            [
                Paragraph("<b>Quality Gate:</b>", S["label"]),
                Paragraph(f"<font color='{q_status_color}'><b>{q_status_txt}</b></font>", S["body"]),
                Paragraph("<b>Sufficient for Assessment:</b>", S["label"]),
                Paragraph("<b>Yes</b>" if q_suf else "<b>No</b>", S["body"]),
            ],
            [
                Paragraph("<b>Duration:</b>", S["label"]),
                Paragraph(f"{q_det.get('duration_sec', 'N/A')} s", S["body"]),
                Paragraph("<b>Sampling Rate:</b>", S["label"]),
                Paragraph(f"{q_det.get('sfreq_hz', 'N/A')} Hz", S["body"]),
            ],
            [
                Paragraph("<b>Channels:</b>", S["label"]),
                Paragraph(str(q_det.get("n_channels", "N/A")), S["body"]),
                Paragraph("<b>Flat Channels:</b>", S["label"]),
                Paragraph(str(q_det.get("n_flat_channels", 0)), S["body"]),
            ],
        ]
        q_tbl = Table(q_rows, colWidths=[90, 165, 120, 165])
        q_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), C_BG),
            ("BOX",        (0,0), (-1,-1), 0.5, C_BORDER),
            ("VALIGN",     (0,0), (-1,-1), "TOP"),
            ("TOPPADDING", (0,0), (-1,-1), 3),
            ("BOTTOMPADDING",(0,0),(-1,-1),3),
            ("LEFTPADDING",(0,0),(-1,-1), 6),
        ]))
        story.append(q_tbl)

        for flag in q_flags:
            story.append(Paragraph(f"⚠ <b>Flag:</b> {flag}", S["body"]))
        for warn in q_warns:
            story.append(Paragraph(f"ℹ <b>Warning:</b> {warn}", S["muted"]))

        story.append(Paragraph(
            f"<i>Quality thresholds: {qr.get('thresholds_label', 'HEURISTIC_BASELINE')} — "
            "not calibrated against an external benchmark dataset.</i>",
            S["muted"],
        ))
        _sp(story, 8)

    # ------------------------------------------------------------------ #
    # 5. Dimension Risk Breakdown
    # ------------------------------------------------------------------ #
    story.append(Paragraph("<b>DIMENSION RISK BREAKDOWN</b>", S["sec"]))
    dim_header = [
        Paragraph("<b>Dimension</b>",              S["label"]),
        Paragraph("<b>Score</b>",                  S["label"]),
        Paragraph("<b>Level</b>",                  S["label"]),
        Paragraph("<b>Method</b>",                 S["label"]),
        Paragraph("<b>Assessment Finding</b>",     S["label"]),
    ]
    dim_rows = [dim_header]
    for dim in audit.get("dimensions", []):
        dfg, _ = _risk_colors(dim.get("level", "LOW"))
        dim_rows.append([
            Paragraph(f"<b>{dim.get('label', dim.get('key', ''))}</b>", S["body"]),
            Paragraph(f"<b>{dim.get('score', 0)}</b> / 100",            S["body"]),
            Paragraph(
                f"<font color='{dfg.hexval()}'><b>{dim.get('level', 'LOW')}</b></font>",
                S["body"],
            ),
            Paragraph(dim.get("model_type", "HEURISTIC_BASELINE"),      S["muted"]),
            Paragraph(dim.get("explanation", dim.get("summary", "")),    S["body"]),
        ])
    dim_tbl = Table(dim_rows, colWidths=[80, 55, 50, 80, 275])
    dim_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  colors.HexColor("#F1F5F9")),
        ("GRID",          (0,0), (-1,-1), 0.5, C_BORDER),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("RIGHTPADDING",  (0,0), (-1,-1), 5),
    ]))
    story.append(dim_tbl)
    _sp(story, 8)

    # ------------------------------------------------------------------ #
    # 6. Per-dimension evidence (contributing indicators)
    # ------------------------------------------------------------------ #
    story.append(Paragraph("<b>PER-DIMENSION EVIDENCE & CONTRIBUTING INDICATORS</b>", S["sec"]))
    for dim in audit.get("dimensions", []):
        story.append(Paragraph(f"<b>{dim.get('label', '').upper()}</b>", S["subsec"]))
        indicators = dim.get("contributing_indicators", [])
        if indicators:
            for ind in indicators:
                story.append(Paragraph(f"• {ind}", S["bullet"]))
        story.append(Paragraph(dim.get("concern", ""), S["muted"]))
        _sp(story, 4)
    _sp(story, 4)

    # ------------------------------------------------------------------ #
    # 7. Key Findings
    # ------------------------------------------------------------------ #
    key_findings = audit.get("keyFindings", [])
    if key_findings:
        story.append(Paragraph("<b>KEY PRIVACY EXPOSURE FINDINGS</b>", S["sec"]))
        fi_rows = [[
            Paragraph("•", S["body"]),
            Paragraph(f, S["body"]),
        ] for f in key_findings]
        fi_tbl = Table(fi_rows, colWidths=[12, 528])
        fi_tbl.setStyle(TableStyle([
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ("TOPPADDING",    (0,0), (-1,-1), 2),
        ]))
        story.append(fi_tbl)
        _sp(story, 8)

    # ------------------------------------------------------------------ #
    # 8. Recommendations
    # ------------------------------------------------------------------ #
    recommendations = audit.get("recommendations", [])
    if recommendations:
        story.append(Paragraph("<b>PRIORITISED PRIVACY MITIGATION RECOMMENDATIONS</b>", S["sec"]))

        for rec in recommendations[:8]:
            pfg      = _priority_color(rec.get("priority", "MEDIUM"))
            evidence = rec.get("evidence", [])
            impl     = rec.get("implementation", [])
            impact   = rec.get("expected_impact", "REQUIRES_EMPIRICAL_VALIDATION")
            residual = rec.get("residual_risk",   "UNKNOWN")
            ev_stat  = rec.get("evidence_status", "HEURISTIC_BASELINE")
            threat   = rec.get("threat", "")

            rec_content = [
                Paragraph(
                    f"<b>{rec.get('number','')} {rec.get('title','')}</b>  "
                    f"[<font color='{pfg.hexval()}'><b>{rec.get('priority','?')} PRIORITY</b></font>]  "
                    f"<font color='#64748B'>Dimension: {rec.get('risk_dimension', '?')}</font>",
                    S["body"],
                ),
            ]
            if threat:
                rec_content.append(Paragraph(f"<b>Threat:</b> {threat}", S["muted"]))
            if evidence:
                rec_content.append(Paragraph("<b>Evidence:</b> " + "; ".join(evidence), S["muted"]))

            rec_content.append(Paragraph(f"<b>Reason:</b> {rec.get('reason', rec.get('why', ''))}", S["body"]))

            if impl:
                rec_content.append(Paragraph("<b>Implementation:</b>", S["subsec"]))
                for step in impl:
                    rec_content.append(Paragraph(f"  – {step}", S["bullet"]))

            rec_content.append(
                Paragraph(
                    f"<b>Expected impact:</b> {impact}  |  "
                    f"<b>Residual risk:</b> {residual}  |  "
                    f"<b>Evidence status:</b> {ev_stat}",
                    S["muted"],
                )
            )

            rec_tbl = Table([[rec_content]], colWidths=[540])
            rec_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,-1), C_BG),
                ("BOX",           (0,0), (-1,-1), 0.5, C_BORDER),
                ("TOPPADDING",    (0,0), (-1,-1), 5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 5),
                ("LEFTPADDING",   (0,0), (-1,-1), 8),
                ("RIGHTPADDING",  (0,0), (-1,-1), 8),
            ]))
            story.append(KeepTogether(rec_tbl))
            _sp(story, 4)

    _sp(story, 6)

    # ------------------------------------------------------------------ #
    # 9. Limitations & Disclaimer
    # ------------------------------------------------------------------ #
    _hr(story, 0.5)
    story.append(Paragraph("<b>LIMITATIONS & NOTICE</b>", S["sec"]))
    disclaimer = audit.get(
        "disclaimer",
        "NeuroAudit estimates potential privacy exposure from neural data. "
        "Results are model-dependent and should not be interpreted as definitive "
        "statements about an individual's thoughts, emotions, identity, or medical condition.",
    )
    story.append(Paragraph(disclaimer, S["muted"]))
    _sp(story, 4)
    story.append(Paragraph(
        "All risk scores in this report are produced by <b>HEURISTIC_BASELINE models</b>. "
        "These models use domain-knowledge formulas derived from published neuroscience "
        "literature. They have NOT been trained on labelled privacy-exposure ground-truth "
        "data. Quantitative risk-reduction claims for specific controls are not made "
        "unless experimentally validated.",
        S["muted"],
    ))
    _sp(story, 4)
    story.append(Paragraph(
        "Differential Entropy (DE) values are computed over the <i>spatial variance</i> "
        "of absolute band power across recording channels, not over a band-filtered "
        "time series. The notation reflects this scope; full per-channel, per-epoch "
        "DE is planned for the Phase 3 ML integration.",
        S["muted"],
    ))

    # ------------------------------------------------------------------ #
    # Build
    # ------------------------------------------------------------------ #
    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    return pdf
