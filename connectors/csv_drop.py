from __future__ import annotations
import glob, os, pandas as pd
from .base import SensorConnector

class CSVDropConnector(SensorConnector):
    def __init__(self, directory: str, pattern: str="*.csv"):
        self.directory, self.pattern = directory, pattern
    def read(self):
        for path in sorted(glob.glob(os.path.join(self.directory, self.pattern))):
            df = pd.read_csv(path)
            yield from df.to_dict(orient="records")
