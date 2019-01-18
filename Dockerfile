FROM ubuntu:16.04
ENV PYTHONUNBUFFERED 1
# Install Python and Package Libraries
RUN apt-get update && apt-get upgrade -y && apt-get autoremove && apt-get autoclean
RUN apt-get install -y \
    autoconf \
    build-essential \
    libtool \
    libffi-dev \
    libssl-dev \
    libmysqlclient-dev \
    libxml2-dev \
    libxslt-dev \
    libjpeg-dev \
    libfreetype6-dev \
    mysql-server \
    net-tools \
    python-dev \
    python3.5-dev \
    python3-venv \
    python-setools \
    pkg-config \
    python-opengl \
    python-imaging \
    python-pyrex \
    python-pyside.qtopengl \
    supervisor \
    vim \
    virtualenv \
    zlib1g-dev
RUN export LC_ALL="en_US.UTF-8" && export LC_CTYPE="en_US.UTF-8"
# Project Files and Settings
ARG PROJECT=ujumbe
ARG PROJECT_DIR=/var/www/python/${PROJECT}
ARG VIRTUAL_ENV_DIR=/var/www/python/venv/ujumbe/
# Create the virtual environment
RUN python3 -m venv $VIRTUAL_ENV_DIR && source $VIRTUAL_ENV_DIR/bin/activate
RUN git clone https://jerryshikanga@bitbucket.org/jerryshikanga/data_app.git $PROJECT_DIR
WORKDIR $PROJECT_DIR
RUN pip install -r requirements.txt
# telerivet not yet on pip
RUN git clone https://github.com/Telerivet/telerivet-python-client.git && python telerivet-python-client/setup.py install && rm -rf telerivet-python-client
RUN python manage.py makemigrations && python manage.py migrate && python manage.py runscript init_db
# set up loggin files && dirs
RUN mkdir /var/log/ujumbe/
RUN touch $PROJECT_DIR/debug.log && chmod 777 $PROJECT_DIR
# copy supervisor config for gunicorn and celery
RUN cp $PROJECT_DIR/docker/supervisord/gunicorn.conf /etc/supervisor/conf.d/ujumbe_gunicorn.conf
RUN cp $PROJECT_DIR/docker/supervisord/celery.conf /etc/supervisor/conf.d/ujumbe_celery.conf
RUN cp $PROJECT_DIR/docker/supervisord/beat.conf /etc/supervisor/conf.d/ujumbe_celerybeat.conf
RUN cp $PROJETC_DIR/docker/supervisord/group.conf /etc/supervisor/conf.d/group.conf
RUN supervisorctl reread && supervisorctl update
# Server
EXPOSE 8000