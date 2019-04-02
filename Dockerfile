#########################
### build environment ###
#########################

# base image
FROM node:8 as builder

# install chrome for protractor tests
#RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
#RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
#RUN apt-get update && apt-get install -yq google-chrome-stable

# set working directory
RUN mkdir /usr/src/app
WORKDIR /usr/src/app

# add `/usr/src/app/node_modules/.bin` to $PATH
ENV PATH /usr/src/app/node_modules/.bin:$PATH

# install and cache app dependencies
RUN npm install -g npm
COPY ./admin/package.json /usr/src/app/package.json
COPY ./admin/package-lock.json /usr/src/app/package-lock.json
RUN npm install
RUN npm install -g @angular/cli

# add app
COPY ./admin /usr/src/app

# run tests
#RUN ng test --watch=false

# generate build
RUN npm run lint && \
    npm run build-prod


##################
### production ###
##################

FROM python:3-stretch
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
  pip install --upgrade pip && \
  pip install --no-cache-dir -r requirements.txt

VOLUME ["/usr/src/trades", "/usr/src/configs"]

COPY . /usr/src/app
COPY --from=builder /usr/src/app/dist/admin /usr/src/app/API/templates

ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

EXPOSE 3000
CMD ["python3", "main.py", "api"]
