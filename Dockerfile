FROM python:jessie

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

ENV \
  TRADE_DIR=/usr/src/trades \
  TRADE_COMPLETED_DIR=/usr/src/complete_trades \
  CONF_DIR=/usr/src/configs

COPY requirements.txt /usr/src/app/

# setup pyton and other prerequisities
RUN \
  apt-get update && \
  apt-get install -y && \
  pip install --no-cache-dir -r requirements.txt

VOLUME ["/usr/src/trades", "/usr/src/configs"]

COPY . /usr/src/app

CMD ["python3"]

docker run -i -t --rm --name cryptobot \
-v $(pwd)/Trades/Portfolio:/usr/src/trades \
-v $(pwd)/Trades/Completed:/usr/src/complete_trades \
-v $(pwd)/Conf:/usr/src/configs:ro \
cryptobot:0.1 python main.py

-v /etc/localtime:/etc/localtime:ro \