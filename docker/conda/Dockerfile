FROM continuumio/miniconda3:latest

RUN conda install plotly=4.12.0 pandas=1.1.3 numpy=1.19.1 jupyterlab=2.2.6 ipywidgets=7.5.1 ipython=7.18.1 widgetsnbextension=3.5.1 qgrid=1.3.1 pyodbc=4.0.30 beautifulsoup4=4.9.3 lxml=4.6.1 openpyxl pytables fsspec pyyaml html5lib && \
    conda clean --all -f -y 

RUN conda install openpyxl pytables fsspec pyyaml html5lib && conda clean --all -f -y

RUN conda install -c conda-forge/label/gcc7 nodejs && conda clean --all -f -y

RUN conda install -c conda-forge elasticsearch pymysql=0.10.1 pyarrow ipysheet tabulate && conda clean --all -f -y

RUN pip install --quiet --no-cache-dir stix2 taxii2-client splunk-sdk==1.6.13 pandas-profiling yahoo_fin

RUN ipython profile create && jupyter lab --generate-config && \ 
    sed -i "s/# c.NotebookApp.iopub_data_rate_limit = 1000000/c.NotebookApp.iopub_data_rate_limit = 100000000/g" $HOME/.jupyter/jupyter_notebook_config.py

RUN jupyter labextension install --dev-build=True @jupyter-widgets/jupyterlab-manager@2.0.0 && jupyter labextension install --dev-build=True plotlywidget@4.12.0 && \
    jupyter labextension install --dev-build=True jupyterlab-plotly@4.12.0 && jupyter labextension install --dev-build=True qgrid2@1.1.3 && \
    jupyter labextension install --dev-build=True ipysheet &&  conda clean --all -f -y && npm cache clean --force

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

ADD startup_files.sh /root/
RUN /root/startup_files.sh
