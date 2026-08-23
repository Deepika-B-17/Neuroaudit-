"""
SQLite persistence layer for NeuroAudit.

Handles schema initialisation, CRUD operations, and safe serialisation of
audit records.  Accepts both camelCase (pipeline output) and snake_case
(legacy or test-authored) key variants so no translation layer is needed
at the call site.
"""

import os
import json
import sqlite3
from datetime import datetime

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "neuroaudit.db")


# ---------------------------------------------------------------------------
# Key-normalisation helpers
# ---------------------------------------------------------------------------

def _get(d: dict, *keys, default=None):
    """
    Return the value for the first key that exists in *d*.
    Accepts multiple key variants (camelCase then snake_case) so the caller
    does not need to normalise audit dicts before persisting.
    """
    for k in keys:
        if k in d:
            return d[k]
    return default


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def get_db_connection(db_path=None):
    """Establish a connection to the SQLite database."""
    path = db_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def init_db(db_path=None):
    """
    Create the *audits* table and supporting indices if they do not already
    exist.  Safe to call multiple times (idempotent).
    """
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    audit_name TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT,
                    file_size INTEGER DEFAULT 0,
                    description TEXT DEFAULT '',
                    overall_risk INTEGER NOT NULL,
                    risk_level TEXT NOT NULL,
                    overall_summary TEXT NOT NULL,
                    executive_summary TEXT NOT NULL,
                    key_findings TEXT NOT NULL,
                    dimensions TEXT NOT NULL,
                    features TEXT DEFAULT '{}',
                    recommendations TEXT NOT NULL,
                    quality_report TEXT DEFAULT '{}',
                    status TEXT DEFAULT 'Complete',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audits_session_id
                ON audits(session_id);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audits_created_at
                ON audits(created_at DESC);
            """)
            # Add quality_report column to pre-existing databases (migration)
            try:
                conn.execute("ALTER TABLE audits ADD COLUMN quality_report TEXT DEFAULT '{}'")
            except sqlite3.OperationalError:
                pass  # Column already exists
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def save_audit(audit_data: dict, db_path=None):
    """
    Persist or replace an audit record.

    Accepts the raw dict returned by *analyze_eeg_pipeline* (camelCase keys)
    as well as dicts with snake_case keys.  Both variants are handled
    transparently via the *_get* helper.
    """
    init_db(db_path)
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO audits (
                    session_id,
                    audit_name,   file_name,      file_path,     file_size,
                    description,
                    overall_risk, risk_level,
                    overall_summary,  executive_summary,
                    key_findings, dimensions, features, recommendations,
                    quality_report,
                    status,       created_at
                ) VALUES (
                    ?,
                    ?, ?, ?, ?,
                    ?,
                    ?, ?,
                    ?, ?,
                    ?, ?, ?, ?,
                    ?,
                    ?, ?
                )
            """, (
                # Identity
                _get(audit_data, "session_id"),
                # File info – accept camelCase OR snake_case
                _get(audit_data, "auditName",        "audit_name",        default="Untitled Audit"),
                _get(audit_data, "fileName",         "file_name",         default="recording.edf"),
                _get(audit_data, "filePath",         "file_path",         default=""),
                _get(audit_data, "fileSize",         "file_size",         default=0),
                _get(audit_data, "description",                           default=""),
                # Risk
                _get(audit_data, "overallRisk",      "overall_risk",      default=50),
                _get(audit_data, "riskLevel",        "risk_level",        default="MEDIUM"),
                _get(audit_data, "overallSummary",   "overall_summary",   default=""),
                _get(audit_data, "executiveSummary", "executive_summary", default=""),
                # JSON blobs
                json.dumps(_get(audit_data, "keyFindings",    "key_findings",    default=[])),
                json.dumps(_get(audit_data, "dimensions",                        default=[])),
                json.dumps(_get(audit_data, "features",                          default={})),
                json.dumps(_get(audit_data, "recommendations",                   default=[])),
                json.dumps(_get(audit_data, "qualityReport",  "quality_report",  default={})),
                # Metadata
                _get(audit_data, "status",                                default="Complete"),
                _get(audit_data, "createdAt",        "created_at",
                     default=datetime.utcnow().isoformat()),
            ))
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def get_audit(session_id: str, db_path=None):
    """Retrieve a single audit record by *session_id*.  Returns ``None`` if not found."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    try:
        cur = conn.execute(
            "SELECT * FROM audits WHERE session_id = ?", (session_id,)
        )
        row = cur.fetchone()
        return _format_row(row) if row else None
    finally:
        conn.close()


def list_audits(limit: int = 20, db_path=None):
    """Return the *limit* most-recent audit records ordered by creation date."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    try:
        cur = conn.execute(
            "SELECT * FROM audits ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        return [_format_row(row) for row in cur.fetchall()]
    finally:
        conn.close()


def delete_audit(session_id: str, db_path=None):
    """Permanently remove an audit record."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.execute("DELETE FROM audits WHERE session_id = ?", (session_id,))
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Internal row formatter
# ---------------------------------------------------------------------------

def _parse_json(val, default):
    if not val:
        return default
    try:
        return json.loads(val)
    except Exception:
        return default


def _format_row(row) -> dict:
    """Convert a sqlite3.Row into a camelCase audit dict for the frontend."""
    created_raw = row["created_at"] or ""
    try:
        dt = datetime.fromisoformat(created_raw.replace("Z", ""))
        date_str = dt.strftime("%d %b %Y")
    except Exception:
        date_str = created_raw

    return {
        "id":              str(row["id"]),
        "session_id":      row["session_id"],
        "auditName":       row["audit_name"],
        "fileName":        row["file_name"],
        "fileSize":        row["file_size"],
        "description":     row["description"],
        "analysisDate":    date_str,
        "createdAt":       row["created_at"],
        "status":          row["status"],
        "overallRisk":     row["overall_risk"],
        "riskLevel":       row["risk_level"],
        "overallSummary":  row["overall_summary"],
        "executiveSummary": row["executive_summary"],
        "keyFindings":     _parse_json(row["key_findings"],    []),
        "dimensions":      _parse_json(row["dimensions"],      []),
        "features":        _parse_json(row["features"],        {}),
        "recommendations": _parse_json(row["recommendations"], []),
        "qualityReport":   _parse_json(
                               row["quality_report"] if "quality_report" in row.keys() else None,
                               {}
                           ),
    }
