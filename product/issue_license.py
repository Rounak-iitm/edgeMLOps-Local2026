"""Vendor-only license issuer.

Usage requires a vendor-held Ed25519 private key file. Never ship the private key.
"""
from __future__ import annotations
import argparse, base64, json
from pathlib import Path

def canonical(d): return json.dumps({k:v for k,v in d.items() if k!='signature'}, sort_keys=True, separators=(',',':')).encode()

def main():
    p=argparse.ArgumentParser(); p.add_argument('--private-key',required=True); p.add_argument('--customer',required=True); p.add_argument('--site',required=True); p.add_argument('--valid-from',required=True); p.add_argument('--valid-until',required=True); p.add_argument('--out',required=True); a=p.parse_args()
    from cryptography.hazmat.primitives import serialization
    key=serialization.load_pem_private_key(Path(a.private_key).read_bytes(),password=None)
    doc={'license_id':__import__('uuid').uuid4().hex,'customer':a.customer,'site':a.site,'edition':'Enterprise Edge','valid_from':a.valid_from,'valid_until':a.valid_until,'machine_limit':1,'features':['anomaly_detection','predictive_maintenance']}
    doc['signature']=base64.b64encode(key.sign(canonical(doc))).decode()
    Path(a.out).write_text(json.dumps(doc,indent=2),encoding='utf-8')
if __name__=='__main__': main()
