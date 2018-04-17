from threading import Thread
from time import sleep

from binance.client import Client

import asyncio
import websockets
import websockets.exceptions

import os
import os.path

from retrying import retry

# logging.basicConfig(level=logging.DEBUG)

ws_url = 'wss://stream.binance.com:9443/stream?streams=ethbtc@ticker/ontbtc@ticker'

def check_exception(ex):
    return isinstance(ex, (websockets.ConnectionClosed, websockets.InvalidStatusCode))


class BinanceWebsocketThread(Thread):
    def __init__(self, client):
        Thread.__init__(self)
        self.client = client
        self.cancel = False
        self.ws = None
        self.connection_key = None
        self.el = asyncio.new_event_loop()
        self.ticker_ws_future = None
        self.user_ws_future = None


    @retry(
        stop_max_attempt_number=5,
        wait_fixed=1000,
        retry_on_exception=check_exception)
    def run(self):
        asyncio.set_event_loop(self.el)

        get_key = asyncio.ensure_future(self.get_listen_key())
        get_key.add_done_callback(self.listen_key_received)

        self.ticker_ws_future = asyncio.ensure_future(self.ticker_websocket_handler(ws_url))
        asyncio.get_event_loop().run_until_complete(self.ticker_ws_future)

        self.el.close()

    @asyncio.coroutine
    async def get_listen_key(self):
        return self.client.stream_get_listen_key()

    def listen_key_received(self, future):
        key = future.result()
        create_user_ws = False

        if key != self.connection_key or not self.user_ws_future or \
                self.user_ws_future.cancelled() or self.user_ws_future.done():
            create_user_ws = True

        if create_user_ws:
            if self.user_ws_future is not None:
                self.user_ws_future.cancel()

            self.user_ws_future = asyncio.ensure_future(self.user_websocket_handler('wss://stream.binance.com:9443/ws/'+key))

        self.connection_key = key

    async def manage_user_ws_loop(self):
        return self.get_listen_key()

    # @asyncio.coroutine
    # async def ping(self):
    #     while True:
    #         if self.cancel:
    #             return
    #
    #         print('ping')
    #         await asyncio.sleep(1)

    @asyncio.coroutine
    async def user_websocket_handler(self, url):
        if self.cancel:
            return

        async with websockets.connect(url, timeout=1) as websocket:
            print('user ws connected')

            async for message in websocket:
                if self.cancel:
                    return
                print(message)

    @asyncio.coroutine
    async def ticker_websocket_handler(self, url):
        if self.cancel:
            return

        async with websockets.connect(url, timeout=1) as websocket:
            self.ws = websocket
            print('ws connected')

            async for message in websocket:
                if self.cancel:
                    return
                print(message)

    def stop_ws(self):
        self.cancel = True

def main():
    ws_url = 'wss://stream.binance.com:9443/stream?streams=ethbtc@ticker/ontbtc@ticker'
    # ws_url = 'wss://stream.binance.com:9443/?streams=ethbtc@ticker/ontbtc@ticker'

    client = Client(os.environ.get('KEY'), os.environ.get('SECRET'))


    bwst = BinanceWebsocketThread(client)
    bwst.start()
    sleep(5)
    # bwst.stop_ws()



def socket_handler(msg):
    print(msg)

def user_data_handler(msg):
    print(msg)


if __name__ == '__main__':
    main()
