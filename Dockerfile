FROM ubuntu:16.04
RUN apt update && apt upgrade -y
RUN apt install python3-dev python3-pip redis
RUN pip3 install pycryptodome redis
WORKDIR /opts/
COPY . .
