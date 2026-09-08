"""Optional OPC-UA connector. Install opcua when enabled and map node IDs to sensors."""
from __future__ import annotations
from .base import SensorConnector
class OPCUAConnector(SensorConnector):
    def __init__(self, endpoint, node_map):
        try: from opcua import Client
        except ImportError as e: raise RuntimeError("Install optional dependency opcua to use OPC-UA") from e
        self.client=Client(endpoint); self.client.connect(); self.nodes={k:self.client.get_node(v) for k,v in node_map.items()}
    def read(self):
        return [{k: float(node.get_value()) for k,node in self.nodes.items()}]
