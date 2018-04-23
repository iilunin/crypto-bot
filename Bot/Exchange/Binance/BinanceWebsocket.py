import json
import threading
import traceback
from threading import Thread
import time

from binance.client import Client

import asyncio
import websockets
import websockets.exceptions

import signal
import os
import os.path

from retrying import retry
from Utils.Logger import Logger


class BinanceWebsocket(Thread, Logger):
    REFRESH_KEY_TIMEOUT = 30 * 60
    WS_URL = 'wss://stream.binance.com:9443/'
    __EVENT_LOOP = None

    def __init__(self, client: Client):
        Thread.__init__(self)
        Logger.__init__(self)


        self.client = client
        self.stop = False

        self.ticker_websocket = None
        self.user_webscoket = None

        self.ticker_ws_future = None
        self.user_ws_future = None
        self.mngmt_future = None

        self.connection_key = None
        self.user_info_cb = None

        if not BinanceWebsocket.__EVENT_LOOP:
            self.loop = asyncio.get_event_loop()
            BinanceWebsocket.__EVENT_LOOP = self.loop
        else:
            self.loop = BinanceWebsocket.__EVENT_LOOP

        self.time = None

        self.name = 'Binance WebSocket Thread'


    @retry(
        stop_max_attempt_number=3,
        wait_fixed=1000
        # retry_on_exception=BinanceWebsocket.check_exception
    )
    def run(self):
        try:
            asyncio.set_event_loop(self.loop)
            self.mngmt_future = asyncio.ensure_future(self.management_loop())
            self.mngmt_future.add_done_callback(self.feature_finished)
            asyncio.get_event_loop().run_forever()
        finally:
            # self.loop.close()
            pass

    @asyncio.coroutine
    async def management_loop(self):
        while True:
            if self.stop:
                return

            if self.time and (time.time() - self.time) > BinanceWebsocket.REFRESH_KEY_TIMEOUT:
                self.start_user_info()

            await asyncio.sleep(60)

    def start_ticker(self, symbols, callback):
        url = os.path.join(BinanceWebsocket.WS_URL, 'stream?streams=' + '/'.join([s.lower()+'@ticker' for s in symbols]))
        self.ticker_ws_future = asyncio.run_coroutine_threadsafe(self.websocket_handler(url, callback), self.loop)
        self.ticker_ws_future.add_done_callback(self.feature_finished)

    def start_user_info(self, callback=None):
        self.time = time.time()

        if callback:
            self.user_info_cb = callback

        get_key = asyncio.run_coroutine_threadsafe(self.refresh_listen_key(), self.loop)
        get_key.add_done_callback(self.listen_key_received)

    def feature_finished(self, future):
        try:
            self.logInfo('Feature finished: {}'.format(future))
        except Exception as e:
            self.logError(traceback.format_exc())

    @asyncio.coroutine
    async def refresh_listen_key(self):
        return self.client.stream_get_listen_key()

    def listen_key_received(self, future):
        self.stop_user_future()
        key = future.result()
        create_user_ws = False

        if key != self.connection_key or not self.user_ws_future or \
                self.user_ws_future.cancelled() or self.user_ws_future.done():
            create_user_ws = True

        if create_user_ws:
            self.stop_user_future()
            self.user_ws_future = asyncio.ensure_future(
                self.websocket_handler(os.path.join(BinanceWebsocket.WS_URL, 'ws', key), self.user_info_cb))
            self.user_ws_future.add_done_callback(self.feature_finished)

        self.connection_key = key

    async def manage_user_ws_loop(self):
        return self.refresh_listen_key()

    def stop_user_future(self):
        if self.user_ws_future:
            self.user_ws_future.cancel()
            self.user_ws_future = None

    def stop_ticker_future(self):
        if self.ticker_ws_future:
            self.ticker_ws_future.cancel()
            self.ticker_ws_future = None

    @asyncio.coroutine
    async def websocket_handler(self, url, callback):
        if self.stop:
            return

        async with websockets.connect(url, timeout=1) as websocket:
            self.ticker_websocket = websocket
            self.logInfo('Websocket Connected to "{}"'.format(url))

            async for message in websocket:
                if self.stop:
                    return

                if callback:
                    callback(json.loads(message))

    def stop_sockets(self):
        self.stop = True

        self.mngmt_future.cancel()
        self.stop_ticker_future()
        self.stop_user_future()

        self.loop.call_soon_threadsafe(self.loop.stop)

        if threading.current_thread().ident != self.ident:
            self.join()

        self.logInfo('Stopped')
