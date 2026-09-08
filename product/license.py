"""Offline license verification.

The vendor signs licenses outside the customer environment. Only the public
verification key is distributed with the product. Replace PUBLIC_KEY_B64 in a
vendor release with the vendor's Ed25519 public key.
"""
from __future__ import annotations
import base64, json, os
from datetime import date

PUBLIC_KEY_B64 = os.environ.get("EDGEMLOPS_LICENSE_PUBLIC_KEY", "")


def _canonical(doc: dict) -> bytes:
    payload = {k: v for k, v in doc.items() if k != "signature"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def verify_license(path: str, required_feature: str | None = None) -> dict:
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    required = {"license_id","customer","site","edition","valid_from","valid_until","signature"}
    missing = required - set(doc)
    if missing:
        raise ValueError(f"license missing fields: {sorted(missing)}")
    today = date.today()
    if not (date.fromisoformat(doc["valid_from"]) <= today <= date.fromisoformat(doc["valid_until"])):
        raise ValueError("license is outside its validity period")
    if required_feature and required_feature not in doc.get("features", []):
        raise ValueError(f"feature not licensed: {required_feature}")
    if not PUBLIC_KEY_B64:
        raise ValueError("vendor license public key is not configured")
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        key = Ed25519PublicKey.from_public_bytes(base64.b64decode(PUBLIC_KEY_B64))
        key.verify(base64.b64decode(doc["signature"]), _canonical(doc))
    except Exception as exc:
        raise ValueError("license signature verification failed") from exc
    return doc
