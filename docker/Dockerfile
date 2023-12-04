ARG PY_VER="3.10.13-bookworm"

FROM docker.io/library/python:$PY_VER as base_image

RUN apt-get update \
 && apt-get install -qqy \
  build-essential \
  unixodbc unixodbc-dev \
  freetds-dev freetds-bin \
  tdsodbc \
  tesseract-ocr \
  ffmpeg libsm6 libxext6 \
  gnutls-bin \
 && apt-get autoremove -qqy \
 && apt-get autoclean \
 && rm -rf /var/lib/apt/lists/*

RUN echo "[FreeTDS]\n\
Description = FreeTDS unixODBC Driver\n\
Driver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so\n\
Setup = /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so" >> /etc/odbcinst.ini

COPY requirements.txt /tmp/requirements.txt
RUN pip install --trusted-host pypi.python.org -r /tmp/requirements.txt

FROM base_image

LABEL org.opencontainers.image.authors  = "John Omernik <john@omernik.com>" \
      org.opencontainers.image.source   = "https://github.com/JohnOmernik/jupyter_integration_base" \
      org.opencontainers.image.licenses = "Apache 2.0"

RUN ipython profile create && jupyter lab --generate-config \
&& sed -i "s/# c.ServerApp.iopub_data_rate_limit = 1000000/c.ServerApp.iopub_data_rate_limit = 1000000000/g" $HOME/.jupyter/jupyter_lab_config.py

# Recursive dependency?
RUN pip install git+https://github.com/johnomernik/jupyter_integration_base

RUN pip install git+https://github.com/johnomernik/jupyter_splunk
RUN pip install git+https://github.com/johnomernik/jupyter_taxii
RUN pip install git+https://github.com/johnomernik/jupyter_pyodbc
RUN pip install git+https://github.com/johnomernik/jupyter_drill
RUN pip install git+https://github.com/johnomernik/jupyter_tera
RUN pip install git+https://github.com/johnomernik/jupyter_hive
RUN pip install git+https://github.com/johnomernik/jupyter_impala
RUN pip install git+https://github.com/johnomernik/jupyter_oracle
RUN pip install git+https://github.com/johnomernik/jupyter_mssql
RUN pip install git+https://github.com/johnomernik/jupyter_es
RUN pip install git+https://github.com/johnomernik/jupyter_mysql
RUN pip install git+https://github.com/johnomernik/jupyter_dummy
RUN pip install git+https://github.com/johnomernik/jupyter_dtools
RUN pip install git+https://github.com/finleyh/jupyter_urlscan
RUN pip install git+https://github.com/johnomernik/jupyter_mongo
RUN pip install git+https://github.com/johnomernik/qgrid

ADD entrypoint.sh /tmp/entrypoint.sh

ENTRYPOINT ["/bin/bash", "/tmp/entrypoint.sh"]