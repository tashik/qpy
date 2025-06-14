import unittest
from unittest.mock import MagicMock, patch
from qpy.quik_bridge import QuikBridge

# PYTHONPATH=. pytest --maxfail=1 -v tests/test_quik_bridge.py

class TestQuikBridge(unittest.TestCase):
    def setUp(self):
        # Patch JsonProtocolHandler so no real socket is used
        patcher = patch('qpy.quik_bridge.JsonProtocolHandler')
        self.addCleanup(patcher.stop)
        self.MockProtocolHandler = patcher.start()
        self.mock_phandler = self.MockProtocolHandler.return_value
        self.logger = MagicMock()
        self.sock = MagicMock()
        self.bridge = QuikBridge(self.sock, logger=self.logger)

    def test_say_hello(self):
        msg_id = self.bridge.sayHello()
        # Ensure send_request was called with correct arguments
        self.mock_phandler.sendReq.assert_called()
        call_args = self.mock_phandler.sendReq.call_args[0]
        # The second argument is the data dict
        self.assertEqual(call_args[1]['function'], 'PrintDbgStr')
        self.assertEqual(call_args[1]['arguments'], ['Hello from python!'])

    def test_get_classes_list(self):
        msg_id = self.bridge.getClassesList()
        self.mock_phandler.sendReq.assert_called()
        call_args = self.mock_phandler.sendReq.call_args[0]
        self.assertEqual(call_args[1]['function'], 'getClassesList')

    def test_get_security_info(self):
        class_code = 'TQBR'
        sec_code = 'SBER'
        msg_id = self.bridge.getSecurityInfo(class_code, sec_code)
        self.mock_phandler.sendReq.assert_called()
        call_args = self.mock_phandler.sendReq.call_args[0]
        self.assertEqual(call_args[1]['function'], 'getSecurityInfo')
        self.assertEqual(call_args[1]['arguments'], [class_code, sec_code])

    def test_get_class_securities(self):
        class_code = 'TQBR'
        msg_id = self.bridge.getClassSecurities(class_code)
        self.mock_phandler.sendReq.assert_called()
        call_args = self.mock_phandler.sendReq.call_args[0]
        self.assertEqual(call_args[1]['function'], 'getClassSecurities')
        self.assertEqual(call_args[1]['arguments'], [class_code])

    def test_create_ds(self):
        class_code = 'TQBR'
        sec_code = 'SBER'
        interval = '1'
        msg_id = self.bridge.createDs(class_code, sec_code, interval)
        self.mock_phandler.sendReq.assert_called()
        call_args = self.mock_phandler.sendReq.call_args[0]
        self.assertEqual(call_args[1]['function'], 'CreateDataSource')
        self.assertEqual(call_args[1]['arguments'], [class_code, sec_code, interval])

    def test_set_ds_update_callback(self):
        datasource = 'ds1'
        callback = MagicMock()
        msg_id = self.bridge.setDsUpdateCallback(datasource, callback)
        self.mock_phandler.sendReq.assert_called()
        call_args = self.mock_phandler.sendReq.call_args[0]
        self.assertEqual(call_args[1]['function'], 'SetUpdateCallback')
        self.assertEqual(call_args[1]['object'], datasource)

    def test_subscribe_to_quotes_table_params(self):
        class_code = 'TQBR'
        sec_code = 'SBER'
        param_name = 'LAST'
        msg_id = self.bridge.subscribeToQuotesTableParams(class_code, sec_code, param_name)
        self.mock_phandler.sendReq.assert_called()
        call_args = self.mock_phandler.sendReq.call_args[0]
        self.assertEqual(call_args[1]['method'], 'subscribeParamChanges')
        self.assertEqual(call_args[1]['class'], class_code)
        self.assertEqual(call_args[1]['security'], sec_code)
        self.assertEqual(call_args[1]['param'], param_name)

    def test_subscribe_to_orderbook(self):
        class_code = 'TQBR'
        sec_code = 'SBER'
        msg_id = self.bridge.subscribeToOrderBook(class_code, sec_code)
        self.mock_phandler.sendReq.assert_called()
        call_args = self.mock_phandler.sendReq.call_args[0]
        self.assertEqual(call_args[1]['method'], 'subscribeQuotes')
        self.assertEqual(call_args[1]['class'], class_code)
        self.assertEqual(call_args[1]['security'], sec_code)

    def test_close_ds(self):
        datasource = 'ds1'
        msg_id = self.bridge.closeDs(datasource)
        self.mock_phandler.sendReq.assert_called()
        call_args = self.mock_phandler.sendReq.call_args[0]
        self.assertEqual(call_args[1]['function'], 'Close')
        self.assertEqual(call_args[1]['object'], datasource)

if __name__ == '__main__':
    unittest.main()
