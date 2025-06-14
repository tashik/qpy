import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from unittest.mock import MagicMock
from qpy.quik_bridge import QuikBridge
from qpy.event_manager import EVENT_SECURITY_LIST
from qpy.quik_bridge import QMessage

class StubSocket:
    """A minimal socket-like stub for integration testing."""
    def __init__(self):
        self.sent_data = []
    def send(self, data):
        self.sent_data.append(data)
    def setblocking(self, flag):
        pass
    def close(self):
        pass

class TestQuikBridgeIntegration(unittest.TestCase):
    def test_get_class_securities_integration(self):
        # Setup stub socket and bridge
        stub_sock = StubSocket()
        bridge = QuikBridge(stub_sock)

        # Prepare to capture the fired event
        fired_events = []
        def handler(event):
            fired_events.append(event)

        bridge.register(EVENT_SECURITY_LIST, handler)

        # Send the request
        msg_id = bridge.getClassSecurities("TQBR")

        # Simulate a protocol response arriving
        response_event = MagicMock()
        response_event.data = QMessage(msg_id, {
            "result": ["SEC1,SEC2"],
        })
        # Simulate the message_type logic in on_resp
        bridge.message_registry[str(msg_id)].message_type = "class_securities"
        bridge.on_resp(response_event)

        # Assert the event was fired and has the correct type
        self.assertTrue(fired_events)
        self.assertEqual(fired_events[0].type, EVENT_SECURITY_LIST)
        self.assertIn("securities", fired_events[0].data)
        self.assertEqual(fired_events[0].data["securities"], "SEC1,SEC2")

if __name__ == "__main__":
    unittest.main()
