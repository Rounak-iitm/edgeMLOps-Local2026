"""Optional MQTT connector. Install paho-mqtt separately when enabled."""
from __future__ import annotations
import json
from .base import SensorConnector

class MQTTConnector(SensorConnector):
    def __init__(self, broker, topic, **kwargs):
        try: import paho.mqtt.client as mqtt
        except ImportError as e: raise RuntimeError("Install optional dependency paho-mqtt to use MQTT") from e
        self.rows=[]; self.client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, **kwargs)
        self.client.on_message=lambda client, userdata, msg: self.rows.append(json.loads(msg.payload.decode()))
        self.client.connect(broker); self.client.subscribe(topic); self.client.loop_start()
    def read(self):
        rows,self.rows=self.rows,[]
        return rows
