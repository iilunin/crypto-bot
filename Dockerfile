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
