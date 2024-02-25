FROM python:latest

WORKDIR /app
EXPOSE 5000

COPY . /app
RUN apt-get update
RUN apt-get install -y python3-pip sqlite3 ghostscript

RUN rm /app/instance -rf
RUN bash make.sh init
RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn


CMD [ "bash", "make.sh" , "production"]