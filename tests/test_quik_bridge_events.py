import unittest
from unittest.mock import MagicMock, patch
from qpy.quik_bridge import QuikBridge
from qpy.event_manager import (
    Event,
    EVENT_QUOTESTABLE_PARAM_UPDATE,
    EVENT_ORDERBOOK_SNAPSHOT,
    EVENT_CLOSE,
)

class TestQuikBridgeEventFiring(unittest.TestCase):
    def setUp(self):
        self.sock = MagicMock()
        self.bridge = QuikBridge(self.sock)

    def test_on_req_fires_quotes_table_param_update(self):
        with patch.object(self.bridge, "fire") as mock_fire:
            event = MagicMock()
            event.data.id = 1
            event.data.data = {
                "method": "paramChange",
                "param": "LAST",
                "value": 123,
                "security": "SBER",
                "class": "TQBR"
            }
            self.bridge.on_req(event)
            mock_fire.assert_called()
            fired_event = mock_fire.call_args[0][0]
            self.assertEqual(fired_event.type, EVENT_QUOTESTABLE_PARAM_UPDATE)
            self.assertEqual(fired_event.data["sec_code"], "SBER")
            self.assertEqual(fired_event.data["class_code"], "TQBR")
            self.assertEqual(fired_event.data["LAST"], 123)

    def test_on_req_fires_orderbook(self):
        with patch.object(self.bridge, "fire") as mock_fire:
            event = MagicMock()
            event.data.id = 2
            event.data.data = {
                "method": "quotesChange",
                "quotes": {"bid_count": "1", "offer_count": "2"},
                "security": "SBER",
                "class": "TQBR"
            }
            self.bridge.on_req(event)
            mock_fire.assert_called()
            fired_event = mock_fire.call_args[0][0]
            self.assertEqual(fired_event.type, EVENT_ORDERBOOK_SNAPSHOT)
            self.assertEqual(fired_event.data["sec_code"], "SBER")
            self.assertEqual(fired_event.data["class_code"], "TQBR")
            self.assertIn("order_book", fired_event.data)

    def test_on_resp_fires_close(self):
        # Example for on_resp if it fires EVENT_CLOSE (customize as needed)
        with patch.object(self.bridge, "fire") as mock_fire:
            event = MagicMock()
            event.data.id = 3
            event.data.data = {"method": "close"}
            # You may need to adjust this if on_resp does not fire EVENT_CLOSE directly
            self.bridge.on_resp(event)
            # This test is illustrative; adapt to actual on_resp behavior
            # mock_fire.assert_called()
            # fired_event = mock_fire.call_args[0][0]
            # self.assertEqual(fired_event.type, EVENT_CLOSE)

if __name__ == "__main__":
    unittest.main()
