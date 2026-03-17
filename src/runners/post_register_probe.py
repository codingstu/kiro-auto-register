import json
import os
import requests
from pathlib import Path
from datetime import datetime

OIDC_TOKEN_URL = "https://oidc.us-east-1.amazonaws.com/token"
MODELS_URL = "https://codewhisperer.us-east-1.amazonaws.com/ListAvailableModels?targetService=codium&workspaceContext=%7B%7D"


def build_credentials_from_accounts(
    accounts_path: Path,
    output_all_path: Path,
    output_latest_path: Path,
):
    if not accounts_path.exists():
        print(f"⚠️ 未找到账号文件: {accounts_path}")
        output_all_path.write_text("[]", encoding="utf-8")
        return []

    accounts = json.loads(accounts_path.read_text(encoding="utf-8"))
    creds = []

    for item in accounts:
        if item.get("status") != "aws_sso_authorized":
            continue
        refresh_token = item.get("aws_sso_refresh_token", "")
        client_id = item.get("aws_sso_client_id", "")
        client_secret = item.get("aws_sso_client_secret", "")
        access_token = item.get("aws_sso_access_token", "")
        if not (refresh_token and client_id and client_secret):
            continue

        creds.append(
            {
                "refreshToken": refresh_token,
                "accessToken": access_token,
                "clientId": client_id,
                "clientSecret": client_secret,
                "email": item.get("email", ""),
                "createdAt": item.get("created_at", ""),
            }
        )

    output_all_path.write_text(
        json.dumps(creds, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if creds:
        latest = {
            "refreshToken": creds[-1]["refreshToken"],
            "accessToken": creds[-1]["accessToken"],
            "clientId": creds[-1]["clientId"],
            "clientSecret": creds[-1]["clientSecret"],
        }
        output_latest_path.write_text(
            json.dumps(latest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print(f"✅ 已生成全部凭证: {output_all_path} ({len(creds)} 条)")
    return creds


def probe_credential(credential: dict, timeout: int = 25):
    payload = {
        "clientId": credential.get("clientId", ""),
        "clientSecret": credential.get("clientSecret", ""),
        "grantType": "refresh_token",
        "refreshToken": credential.get("refreshToken", ""),
    }

    try:
        refresh_resp = requests.post(OIDC_TOKEN_URL, json=payload, timeout=timeout)
    except Exception as exc:
        return {
            "ok": False,
            "stage": "refresh",
            "refresh_status": None,
            "models_status": None,
            "error": f"refresh_request_error: {exc}",
        }

    if refresh_resp.status_code != 200:
        return {
            "ok": False,
            "stage": "refresh",
            "refresh_status": refresh_resp.status_code,
            "models_status": None,
            "error": refresh_resp.text[:1200],
        }

    try:
        refresh_data = refresh_resp.json()
        access_token = refresh_data.get("accessToken", "")
    except Exception as exc:
        return {
            "ok": False,
            "stage": "refresh",
            "refresh_status": refresh_resp.status_code,
            "models_status": None,
            "error": f"refresh_json_error: {exc}",
        }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    try:
        models_resp = requests.get(MODELS_URL, headers=headers, timeout=timeout)
    except Exception as exc:
        return {
            "ok": False,
            "stage": "models",
            "refresh_status": refresh_resp.status_code,
            "models_status": None,
            "error": f"models_request_error: {exc}",
        }

    if models_resp.status_code != 200:
        return {
            "ok": False,
            "stage": "models",
            "refresh_status": refresh_resp.status_code,
            "models_status": models_resp.status_code,
            "error": models_resp.text[:1200],
        }

    model_count = 0
    try:
        model_payload = models_resp.json()
        model_count = len(model_payload.get("models", []))
    except Exception:
        model_count = 0

    return {
        "ok": True,
        "stage": "models",
        "refresh_status": refresh_resp.status_code,
        "models_status": models_resp.status_code,
        "error": "",
        "modelCount": model_count,
    }


def run_post_probe(base_dir: Path, probe_timeout: int = 25):
    key_dir = base_dir / "key"
    key_dir.mkdir(parents=True, exist_ok=True)

    accounts_path = key_dir / "accounts.json"
    all_credentials_path = key_dir / "kiro_go_credentials_all.json"
    latest_credential_path = key_dir / "kiro_go_credential_latest.json"

    credentials = build_credentials_from_accounts(
        accounts_path=accounts_path,
        output_all_path=all_credentials_path,
        output_latest_path=latest_credential_path,
    )

    probe_results = []
    available = []
    suspended = []
    unknown = []

    for idx, credential in enumerate(credentials, start=1):
        email = credential.get("email", "")
        print(f"🔎 探测账号 {idx}/{len(credentials)}: {email}")
        result = probe_credential(credential, timeout=probe_timeout)

        row = {
            "index": idx,
            "email": email,
            "refresh_status": result.get("refresh_status"),
            "models_status": result.get("models_status"),
            "ok": result.get("ok"),
            "stage": result.get("stage"),
            "error": result.get("error", ""),
            "checkedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        probe_results.append(row)

        if result.get("ok"):
            available.append(credential)
        elif "TEMPORARILY_SUSPENDED" in (result.get("error") or ""):
            item = dict(credential)
            item["probeStage"] = row["stage"]
            item["probeStatus"] = row["models_status"] or row["refresh_status"]
            item["probeError"] = row["error"]
            suspended.append(item)
        else:
            item = dict(credential)
            item["probeStage"] = row["stage"]
            item["probeStatus"] = row["models_status"] or row["refresh_status"]
            item["probeError"] = row["error"]
            unknown.append(item)

    (key_dir / "kiro_account_probe_result.json").write_text(
        json.dumps(probe_results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (key_dir / "kiro_go_credentials_available.json").write_text(
        json.dumps(available, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (key_dir / "kiro_go_credentials_suspended.json").write_text(
        json.dumps(suspended, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    summary = {
        "totalCredentials": len(credentials),
        "totalProbed": len(probe_results),
        "availableCount": len(available),
        "suspendedCount": len(suspended),
        "unknownCount": len(unknown),
        "availableFile": "key/kiro_go_credentials_available.json",
        "suspendedFile": "key/kiro_go_credentials_suspended.json",
        "sourceProbeFile": "key/kiro_account_probe_result.json",
    }
    (key_dir / "kiro_go_probe_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        "✅ 探测完成: "
        f"总数={summary['totalCredentials']}, "
        f"可用={summary['availableCount']}, "
        f"封禁={summary['suspendedCount']}, "
        f"未知={summary['unknownCount']}"
    )
    return summary


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    timeout = int(os.getenv("PROBE_TIMEOUT", "25"))
    run_post_probe(project_root, probe_timeout=timeout)
