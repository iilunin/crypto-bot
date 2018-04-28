from time import sleep

from binance.client import Client

import os
import os.path

from Bot.Exchange.Binance.BinanceWebsocket import BinanceWebsocket


def main():

    client = Client(os.environ.get('KEY'), os.environ.get('SECRET'))

    for _ in range(1, 10):
        print('Creating BinanceWebsocketThread instance')
        bwst = BinanceWebsocket(client)

        # signal.signal(signal.SIGINT, lambda sig, frame: bwst.stop_ws())
        # signal.signal(signal.SIGTERM, lambda sig, frame: bwst.stop_ws())
        bwst.start_ticker(['ontbtc'], callback=lambda msg: print(msg))
        bwst.start_user_info(callback=lambda msg: print(msg))
        bwst.start()

        print('sleep')
        sleep(10)
        bwst.stop_ticker_future()
        bwst.start_ticker(['ETHBTC'], callback=lambda msg: print(msg))
        sleep(10)
        bwst.stop_sockets()
        # sleep(1)

    # bwst.user_webscoket.close()




def socket_handler(msg):
    print(msg)

def user_data_handler(msg):
    print(msg)


if __name__ == '__main__':
    main()
