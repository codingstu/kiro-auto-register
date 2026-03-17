import json
from pathlib import Path
from datetime import datetime


def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _mask(value: str, keep=6):
    if not value:
        return ""
    if len(value) <= keep:
        return "*" * len(value)
    return value[:keep] + "***"


def build_bundle(base_dir: Path):
    key_dir = base_dir / "key"
    probe_summary = _read_json(key_dir / "kiro_go_probe_summary.json", {})
    probe_rows = _read_json(key_dir / "kiro_account_probe_result.json", [])
    accounts = _read_json(key_dir / "accounts.json", [])

    suspended_rows = [r for r in probe_rows if (r.get("category") == "suspended" or "TEMPORARILY_SUSPENDED" in (r.get("error") or ""))]
    suspended_emails = {r.get("email", "") for r in suspended_rows if r.get("email")}

    account_evidence = []
    for acc in accounts:
        email = acc.get("email", "")
        if email not in suspended_emails:
            continue
        account_evidence.append({
            "email": email,
            "created_at": acc.get("created_at", ""),
            "status": acc.get("status", ""),
            "aws_sso_client_id": _mask(acc.get("aws_sso_client_id", ""), keep=8),
            "aws_sso_refresh_token": _mask(acc.get("aws_sso_refresh_token", ""), keep=8),
        })

    bundle = {
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": probe_summary,
        "suspendedCount": len(suspended_rows),
        "suspendedAccounts": account_evidence,
        "suspensionReasons": [
            {
                "email": row.get("email", ""),
                "reason": row.get("reason", ""),
                "models_status": row.get("models_status"),
                "refresh_status": row.get("refresh_status"),
                "checkedAt": row.get("checkedAt", ""),
            }
            for row in suspended_rows
        ],
        "notes": [
            "This bundle is intended for official support review and identity verification.",
            "Sensitive token fields are masked intentionally.",
        ],
    }

    output = key_dir / "kiro_support_bundle.json"
    output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    return output, bundle


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    out, data = build_bundle(root)
    print(f"Support bundle written: {out}")
    print(f"Suspended accounts: {data.get('suspendedCount', 0)}")
