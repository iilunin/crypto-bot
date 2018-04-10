FROM python:jessie
MAINTAINER Igor Ilunin <ilunin.igor@gmail.com>

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

ENV \
  TRADE_DIR=/usr/src/trades \
  TRADE_COMPLETED_DIR=/usr/src/complete_trades \
  CONF_DIR=/usr/src/configs

COPY requirements.txt /usr/src/app/

RUN \
  apt-get update && \
  apt-get install -y && \
  apt-get install -y tzdata && \
  pip install --no-cache-dir -r requirements.txt

VOLUME ["/usr/src/trades", "/usr/src/configs"]

COPY . /usr/src/app

ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

CMD ["python3", "main.py"]

#docker run -i -t --rm --privileged --name cryptobot \
#-e "TZ=America/New_York" \
#-v $(pwd)/Trades/Portfolio:/usr/src/trades \
#-v $(pwd)/Trades/Completed:/usr/src/complete_trades \
#-v $(pwd)/Conf:/usr/src/configs:ro \
#-v /etc/localtime:/etc/localtime:ro \
#cryptobot

#docker run -d --name cryptobot \
#-v $(pwd)/Trades/Portfolio:/usr/src/trades \
#-v $(pwd)/Trades/Completed:/usr/src/complete_trades \
#-v $(pwd)/Conf:/usr/src/configs:ro \
#cryptobot:latest