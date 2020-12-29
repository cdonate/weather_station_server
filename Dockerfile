FROM python:3.5

ARG LOG_LEVEL
ENV LOG_LEVEL_ENV ${LOG_LEVEL}

ARG PORT
ENV PORT_ENV ${PORT}

ARG GUNICORN_WORKERS
ENV GUNICORN_WORKERS_ENV ${GUNICORN_WORKERS}


ADD . /weather_station_api
WORKDIR /weather_station_api

# This is for you use the POSTGRES with SQLAlchemy
RUN apt-get update -y
RUN apt-get install -y ssh \
postgresql \
python-psycopg2 \
libpq-dev \
python3-dev \
coreutils \
vim

RUN pip install -r requirements.txt
RUN export $(cat .env | xargs)
EXPOSE $PORT

CMD gunicorn -w ${GUNICORN_WORKERS_ENV} -b 0.0.0.0:${PORT_ENV} app.initialize:web_app --log-level=${LOG_LEVEL_ENV}