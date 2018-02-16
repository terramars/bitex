# Import Built-Ins
import logging
import json
import threading
import time

# Import Third-Party
from websocket import create_connection, WebSocketTimeoutException
import requests
# Import Homebrew
from bitex.api.WSS.base import WSSAPI

# Init Logging Facilities
log = logging.getLogger(__name__)


class PoloniexWSS(WSSAPI):
    def __init__(self, pairs=None):
        super(PoloniexWSS, self).__init__('wss://api2.poloniex.com/', 'Poloniex')
        self.conn = None
        #TODO: pairs => pair_id
        # https://poloniex.com/public?command=returnTicker
        self.pair_id_map = {
            # Actually USDT_BTC....
            'BTCUSD': '121',
            # USDT_ETH
            'ETHUSD': '149',


        }
        self.id_pair_map = {v: k for k, v in self.pair_id_map.items()}
        if not pairs:
            pairs = ['148']
        else:
            self.pairs = [self.pair_id_map[pair] for pair in pairs]
        self._data_thread = None

    def start(self):
        super(PoloniexWSS, self).start()

        self._data_thread = threading.Thread(target=self._process_data)
        self._data_thread.daemon = True
        self._data_thread.start()

    def stop(self):
        super(PoloniexWSS, self).stop()

        self._data_thread.join()

    def _process_data(self):
        self.conn = create_connection(self.addr, timeout=4)
        # subscribe in loop
        for pair in self.pairs:
            payload = json.dumps({'command': 'subscribe', 'channel': pair})
            self.conn.send(payload)

        while self.running:
            try:
                data = json.loads(self.conn.recv())
            except (WebSocketTimeoutException, ConnectionResetError):
                self._controller_q.put('restart')
            
            pair_id = data[0]
            seq_id = data[1]
            updates = data[2]
            if True:
                self.data_q.put(('order_book', self.id_pair_map[str(pair_id)],
                                 updates, time.time()))
        self.conn = None
