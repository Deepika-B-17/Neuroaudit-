import urllib.request
import json
import os

def test_live_api():
    base_url = "http://127.0.0.1:5000/api"

    # 1. Health
    with urllib.request.urlopen(f"{base_url}/health") as res:
        health = json.loads(res.read().decode())
        print(f"[OK] Health: {health}")
        assert health["status"] == "healthy"

    # 2. Samples
    with urllib.request.urlopen(f"{base_url}/samples") as res:
        samples_data = json.loads(res.read().decode())
        samples = samples_data["samples"]
        print(f"[OK] Fetched {len(samples)} benchmark samples.")
        assert len(samples) >= 3

    # 3. Load Sample
    req_data = json.dumps({
        "sample_id": "session_a_rest_eeg.edf",
        "auditName": "Live Verification Audit",
        "description": "Verifying full live pipeline execution."
    }).encode("utf-8")

    req = urllib.request.Request(f"{base_url}/samples/load", data=req_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        audit = json.loads(res.read().decode())
        session_id = audit["session_id"]
        print(f"[OK] Loaded Sample Audit: Session={session_id}, Risk={audit['overallRisk']} ({audit['riskLevel']})")
        print(f"     Executive Summary: {audit['executiveSummary'][:80]}...")
        assert "dimensions" in audit
        assert len(audit["dimensions"]) == 4

    # 4. Fetch Analysis
    with urllib.request.urlopen(f"{base_url}/analysis/{session_id}") as res:
        fetched_audit = json.loads(res.read().decode())
        print(f"[OK] Fetched Analysis for session {session_id}: {fetched_audit['auditName']}")
        assert fetched_audit["session_id"] == session_id

    # 5. Fetch Recommendations
    with urllib.request.urlopen(f"{base_url}/recommendations/{session_id}") as res:
        recs_data = json.loads(res.read().decode())
        recs = recs_data["recommendations"]
        print(f"[OK] Fetched {len(recs)} Recommendations. Top recommendation: {recs[0]['title']} ({recs[0]['priority']})")
        assert len(recs) >= 3

    # 6. Download PDF Report
    with urllib.request.urlopen(f"{base_url}/report/{session_id}/download") as res:
        pdf_bytes = res.read()
        print(f"[OK] Generated & Downloaded PDF: {len(pdf_bytes)} bytes.")
        assert pdf_bytes.startswith(b"%PDF")

    # 7. Recent Audits List
    with urllib.request.urlopen(f"{base_url}/audits") as res:
        audits_data = json.loads(res.read().decode())
        audits = audits_data["audits"]
        print(f"[OK] Database Audits Count: {len(audits)}")
        assert len(audits) >= 1

    print("\n>>> ALL LIVE BACKEND API VERIFICATIONS PASSED 100%! <<<")

if __name__ == "__main__":
    test_live_api()
