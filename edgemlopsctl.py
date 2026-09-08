from __future__ import annotations
import argparse, json, os, subprocess, sys, urllib.request
ROOT=os.path.dirname(os.path.abspath(__file__))
COMPOSE=os.path.join(ROOT,"docker","docker-compose.yml")
ENV=os.path.join(ROOT,"docker",".env")

def compose(*args):
    return subprocess.run(["docker","compose","--env-file",ENV,"-f",COMPOSE,*args], cwd=ROOT, check=False).returncode

def health():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=3) as r:
            print(json.dumps(json.load(r), indent=2))
    except Exception as e:
        print(f"UNAVAILABLE: {e}"); return 1
    return 0

def main():
    p=argparse.ArgumentParser(prog="edgemlopsctl", description="EdgeMLOps Enterprise Edge operations CLI")
    sub=p.add_subparsers(dest="cmd", required=True)
    for name in ("start","stop","restart","status","logs","update"):
        sub.add_parser(name)
    a=p.parse_args()
    if a.cmd=="start": return compose("up","-d")
    if a.cmd=="stop": return compose("down")
    if a.cmd=="restart": return compose("restart")
    if a.cmd=="update": return compose("up","-d","--build")
    if a.cmd=="logs": return compose("logs","--tail","200")
    return health()
if __name__ == "__main__": sys.exit(main())
