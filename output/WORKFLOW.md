# EdgeMLOps Workflow

```mermaid
flowchart LR
    A[Sensor Inputs\nCSV / MQTT / OPC-UA / Simulator] --> B[Reference and Live Batches]
    B --> C[Drift Detection\nKS / PSI]
    C -->|No drift| D[Keep Active Model]
    C -->|Drift detected| E[Retrain Model]
    E --> F[Convert to ONNX]
    F --> G[ONNX Runtime Validation]
    G --> H[Versioned Model Store]
    H --> I[Update LATEST Pointer]
    I --> J[FastAPI Inference Service]
    J --> K[Predictions\nHealth / Model Info]
    H --> L[Filesystem Watcher]
    L --> J
    M[ZenML Dashboard] -. Pipeline Runs and Artifacts .-> B
    M -. Monitoring .-> E
```

## Workflow Summary

1. Sensor data enters through a connector or simulator.
2. Reference and live batches are compared for distribution drift.
3. A no-drift result keeps the current model active.
4. Detected drift triggers local retraining.
5. The trained model is converted to ONNX.
6. ONNX Runtime validates the model before publication.
7. The validated model is stored as a versioned artifact.
8. The `LATEST` pointer identifies the active model.
9. FastAPI serves local predictions.
10. The filesystem watcher hot-reloads newly deployed models.
11. ZenML records pipeline runs and artifacts.
