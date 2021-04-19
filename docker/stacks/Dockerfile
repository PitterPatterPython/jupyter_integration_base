
ARG BASE_CONTAINER=jupyter/scipy-notebook:latest

FROM $BASE_CONTAINER

USER $NB_UID

RUN conda install --quiet --yes qgrid pyodbc lxml openpyxl html5lib && \
    conda clean --all -f -y && fix-permissions "${CONDA_DIR}" && fix-permissions "/home/${NB_USER}"

RUN conda install --quiet --yes -c plotly plotly=4.14.3 && \
    conda clean --all -f -y && fix-permissions "${CONDA_DIR}" && fix-permissions "/home/${NB_USER}"

RUN conda install -c conda-forge --quiet --yes elasticsearch pymysql=0.10.1 pyarrow ipysheet tabulate && \
    conda clean --all -f -y && fix-permissions "${CONDA_DIR}" && fix-permissions "/home/${NB_USER}"

RUN pip install --quiet --no-cache-dir stix2 taxii2-client splunk-sdk==1.6.13 pandas-profiling yahoo-fin && \
    fix-permissions "${CONDA_DIR}" && fix-permissions "/home/${NB_USER}"

RUN ipython profile create && fix-permissions "${CONDA_DIR}" && fix-permissions "/home/${NB_USER}"

RUN jupyter labextension install --dev-build=True @jupyter-widgets/jupyterlab-manager && jupyter labextension install --dev-build=True plotlywidget@4.14.3 && \
    jupyter labextension install --dev-build=True jupyterlab-plotly@4.14.3 && jupyter labextension install --dev-build=True @j123npm/qgrid2@1.1.4 && \
    jupyter labextension install --dev-build=True ipysheet && \
    conda clean --all -f -y && npm cache clean --force && fix-permissions "${CONDA_DIR}" && fix-permissions "/home/${NB_USER}"

RUN git clone https://github.com/johnomernik/jupyter_integration_base && cd jupyter_integration_base && python setup.py install && cd .. && rm -rf ./jupyter_integration_base
RUN git clone https://github.com/johnomernik/jupyter_splunk && cd jupyter_splunk && python setup.py install && cd .. && rm -rf ./jupyter_splunk
RUN git clone https://github.com/johnomernik/jupyter_drill && cd jupyter_drill && python setup.py install && cd .. && rm -rf ./jupyter_drill
RUN git clone https://github.com/johnomernik/jupyter_pyodbc && cd jupyter_pyodbc && python setup.py install && cd .. && rm -rf ./jupyter_pyodbc
RUN git clone https://github.com/johnomernik/jupyter_impala && cd jupyter_impala && python setup.py install && cd .. && rm -rf ./jupyter_impala
RUN git clone https://github.com/johnomernik/jupyter_hive && cd jupyter_hive && python setup.py install && cd .. && rm -rf ./jupyter_hive
RUN git clone https://github.com/johnomernik/jupyter_tera && cd jupyter_tera && python setup.py install && cd .. && rm -rf ./jupyter_tera
RUN git clone https://github.com/johnomernik/jupyter_es && cd jupyter_es && python setup.py install && cd .. && rm -rf ./jupyter_es
RUN git clone https://github.com/johnomernik/jupyter_mysql && cd jupyter_mysql && python setup.py install && cd .. && rm -rf ./jupyter_mysql
RUN git clone https://github.com/johnomernik/jupyter_taxii && cd jupyter_taxii && python setup.py install && cd .. && rm -rf ./jupyter_taxii

ADD startup_files.sh /home/${NB_USER}
RUN /home/${NB_USER}/startup_files.sh



