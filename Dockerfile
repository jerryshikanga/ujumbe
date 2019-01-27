FROM ubuntu:16.04
ENV PYTHONUNBUFFERED 1
# Install Python and Package Libraries
RUN apt-get update && apt-get upgrade -y && apt-get autoremove && apt-get autoclean && apt-get install -y --no-install-recommends apt-utils
RUN apt-get install -y \
    autoconf \
    build-essential \
    git \
    libtool \
    libmysqlclient-dev \
    libssl-dev \
    libxml2-dev \
    net-tools \
    python-dev \
    python3-venv \
    pkg-config \
    supervisor \
    virtualenv \
    wget \
    zlib1g-dev
RUN export LC_ALL="en_US.UTF-8" && export LC_CTYPE="en_US.UTF-8"
#install rabbitmq
RUN apt-key adv --keyserver "hkps.pool.sks-keyservers.net" --recv-keys "0x6B73A36E6026DFCA"
RUN wget -O - "https://github.com/rabbitmq/signing-keys/releases/download/2.0/rabbitmq-release-signing-key.asc" | apt-key add -
RUN echo "deb http://dl.bintray.com/rabbitmq-erlang/debian xenial erlang" >> /etc/apt/sources.list.d/bintray.erlang.list
RUN echo "127.0.0.1 $(hostname -s)" | tee -a /etc/hosts
RUN apt-get update && apt-get -y install erlang-nox && apt-get --fix-broken install
#&& systemctl start rabbitmq-server
# Project Files and Settings
ARG PROJECT=ujumbe
ARG PROJECT_DIR=/var/www/python/${PROJECT}/
ARG VIRTUAL_ENV_DIR=/var/www/python/venv/${PROJECT}/
# Create the virtual environment
RUN python3 -m venv $VIRTUAL_ENV_DIR
RUN $VIRTUAL_ENV_DIR/bin/pip install --upgrade pip
RUN git clone https://jerryshikanga@bitbucket.org/jerryshikanga/data_app.git $PROJECT_DIR
WORKDIR $PROJECT_DIR
RUN $VIRTUAL_ENV_DIR/bin/pip install -r requirements.txt
# telerivet not yet on pypi
RUN git clone https://github.com/Telerivet/telerivet-python-client.git telerivet && $VIRTUAL_ENV_DIR/bin/python telerivet/setup.py install && rm -rf telerivet
ADD ./ujumbe/settings/settings.env $PROJECT_DIR/ujumbe/settings/settings.env
RUN $VIRTUAL_ENV_DIR/bin/python manage.py makemigrations && $VIRTUAL_ENV_DIR/bin/python manage.py migrate && $VIRTUAL_ENV_DIR/bin/python manage.py runscript init_db
# set up logging files && dirs
RUN mkdir /var/log/ujumbe/ && chmod 777 /var/log/ujumbe/
RUN touch $PROJECT_DIR/debug.log && chmod 77 $PROJECT_DIR/debug.log && chmod 777 $PROJECT_DIR
# copy supervisor config for gunicorn and celery
RUN cp $PROJECT_DIR/docker/supervisord/gunicorn.conf /etc/supervisor/conf.d/ujumbe_gunicorn.conf
RUN cp $PROJECT_DIR/docker/supervisord/celery.conf /etc/supervisor/conf.d/ujumbe_celery.conf
RUN cp $PROJECT_DIR/docker/supervisord/beat.conf /etc/supervisor/conf.d/ujumbe_celerybeat.conf
RUN cp $PROJECT_DIR/docker/supervisord/group.conf /etc/supervisor/conf.d/group.conf
RUN service supervisor start && supervisorctl reread && supervisorctl update
# Server
EXPOSE 8000
