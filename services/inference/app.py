"""Production-oriented local edge inference service.

Security defaults:
- /health is public for container orchestration.
- /predict, /model/info and /reload require EDGE_API_KEY when configured.
- API key is supplied with X-API-Key.
- Model updates are validated before becoming active.
"""
from __future__ import annotations
import json, logging, os, threading, time
from typing import Any, Dict, List, Optional
import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

try:
    from product.audit import audit
except Exception:
    def audit(*args, **kwargs): pass

logging.basicConfig(level=os.environ.get("LOG_LEVEL","INFO"),
                    format="%(asctime)s [edge-inference] %(levelname)s %(message)s")
logger=logging.getLogger("edge-inference")
MODEL_STORE_DIR=os.environ.get("MODEL_STORE_DIR","/model_store")
POINTER_FILE=os.path.join(MODEL_STORE_DIR,"LATEST")
METADATA_FILE=os.path.join(MODEL_STORE_DIR,"latest_metadata.json")
API_KEY=os.environ.get("EDGE_API_KEY","").strip()
LICENSE_MODE=os.environ.get("EDGE_LICENSE_MODE","production").strip().lower()
LICENSE_FILE=os.environ.get("EDGE_LICENSE_FILE","").strip()
app=FastAPI(title="EdgeMLOps Local - Enterprise Edge", version="2.0.0",
            docs_url="/docs", redoc_url="/redoc")

class PredictRequest(BaseModel):
    instances: List[List[float]] = Field(min_length=1)

class ModelState:
    def __init__(self):
        self._lock=threading.Lock()
        self.session: Optional[ort.InferenceSession]=None
        self.metadata: Dict[str,Any]={}
        self.loaded_filename: Optional[str]=None
        self.loaded_at: Optional[float]=None
    def load_latest(self)->bool:
        if not os.path.exists(POINTER_FILE): return False
        try:
            filename=open(POINTER_FILE,encoding="utf-8").read().strip()
        except OSError: return False
        if not filename or os.path.basename(filename)!=filename or not filename.endswith(".onnx"):
            logger.error("Invalid LATEST pointer")
            return False
        model_path=os.path.join(MODEL_STORE_DIR,filename)
        if filename==self.loaded_filename: return False
        if not os.path.isfile(model_path): return False
        metadata={}
        try:
            if os.path.exists(METADATA_FILE):
                with open(METADATA_FILE,encoding="utf-8") as f: metadata=json.load(f)
            session=ort.InferenceSession(model_path,providers=["CPUExecutionProvider"])
        except Exception as e:
            logger.error("Rejected model %s: %s",filename,e); return False
        with self._lock:
            self.session=session; self.metadata=metadata
            self.loaded_filename=filename; self.loaded_at=time.time()
        logger.info("Loaded model %s",filename); audit("model_loaded", model=filename); return True
    def predict(self, instances):
        with self._lock: session,metadata=self.session,self.metadata
        if session is None: raise HTTPException(503,"No model loaded yet")
        x=np.asarray(instances,dtype=np.float32)
        expected=len(metadata.get("features",[])) or None
        if x.ndim!=2: raise HTTPException(400,"instances must be a 2D array")
        if expected and x.shape[1]!=expected:
            raise HTTPException(400,f"Expected {expected} features ({metadata.get('features')}), got {x.shape[1]}")
        inp=session.get_inputs()[0].name
        outputs=session.run(None,{inp:x})
        return {o.name:arr.tolist() for o,arr in zip(session.get_outputs(),outputs)}
state=ModelState()

def require_key(x_api_key: Optional[str]):
    if API_KEY and x_api_key!=API_KEY: raise HTTPException(401,"Invalid or missing X-API-Key")

class Handler(FileSystemEventHandler):
    def on_any_event(self,event): state.load_latest()

@app.on_event("startup")
def startup():
    if LICENSE_MODE != "demo":
        if not LICENSE_FILE or not os.path.isfile(LICENSE_FILE):
            raise RuntimeError("A valid customer license is required. Set EDGE_LICENSE_FILE or use demo mode for evaluation only.")
        try:
            from product.license import verify_license
            verify_license(LICENSE_FILE)
        except Exception as exc:
            raise RuntimeError(f"License validation failed: {exc}") from exc
    if LICENSE_MODE != "demo" and not API_KEY:
        raise RuntimeError("EDGE_API_KEY must be configured for production mode")
    os.makedirs(MODEL_STORE_DIR,exist_ok=True)
    state.load_latest()
    obs=Observer(); obs.schedule(Handler(),MODEL_STORE_DIR,recursive=False); obs.daemon=True; obs.start()
    app.state.observer=obs
    logger.info("Watching %s",MODEL_STORE_DIR)

@app.get("/health")
def health():
    return {"status":"ok" if state.session is not None else "waiting_for_model",
            "model_loaded":state.loaded_filename,"version":state.metadata.get("version")}

@app.get("/model/info")
def model_info(x_api_key: Optional[str]=Header(default=None)): 
    require_key(x_api_key)
    if state.session is None: raise HTTPException(503,"No model loaded yet")
    return state.metadata

@app.post("/predict")
def predict(req: PredictRequest,x_api_key: Optional[str]=Header(default=None)):
    require_key(x_api_key); result=state.predict(req.instances); audit("prediction", model=state.loaded_filename, rows=len(req.instances)); return result

@app.post("/reload")
def reload_model(x_api_key: Optional[str]=Header(default=None)):
    require_key(x_api_key); before=state.loaded_filename
    changed=state.load_latest()
    return {"changed":changed,"previous":before,"current":state.loaded_filename}

@app.get("/metrics")
def metrics():
    return {"model_loaded":state.loaded_filename is not None,
            "model_version":state.metadata.get("version"),
            "loaded_at":state.loaded_at}
