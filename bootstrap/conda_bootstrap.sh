#!/bin/bash

C=$(conda)
if [ "$?" -ne 0 ]; then
    echo "conda doesn't seem to be installed - exiting"
    exit 1
fi


G=$(git --version)
if [ "$?" -ne 0 ]; then
    echo "git doesn't seem to be installed - exiting"
    exit 1
fi


export CONDA_ALWAYS_YES="true"


if [ -z "$1"  ]; then
    JUPENV="juplab"
else
    JUPENV="$1"
fi

echo ""
echo "Using ${JUPENV} for conda environment"
echo "Creating env"
echo ""

conda create -n $JUPENV
source activate $JUPENV

echo ""
echo "Installing packages"
echo ""

conda install plotly=4.12.0 pandas=1.1.3 numpy=1.19.1 jupyterlab=2.2.6 ipywidgets=7.5.1 ipython=7.18.1 widgetsnbextension=3.5.1 qgrid=1.3.1 pyodbc=4.0.30 beautifulsoup4=4.9.3 lxml=4.6.1
conda install -c conda-forge/label/gcc7 nodejs
conda install -c conda-forge pandas-profiling pymysql=0.10.1 elasticsearch



git clone https://github.com/splunk/splunk-sdk-python && cd splunk-sdk-python && python setup.py install && cd .. && rm -rf ./splunk-sdk-python

echo ""
echo "Installing extensions"
echo ""
jupyter labextension install @jupyter-widgets/jupyterlab-manager
jupyter labextension install plotlywidget@4.12.0
jupyter labextension install jupyterlab-plotly@4.12.0
jupyter labextension install qgrid2


echo ""
echo "Installing Jupyter Integrations"
echo ""

echo " - Base Jupyter Integrations"
cd .. && python setup.py install && cd bootstrap

CUR_BASE="https://github.com/johnomernik"

CUR_INT="splunk"
CUR_REPO="jupyter_${CUR_INT}"
echo ""
echo "$CUR_REPO"
echo ""
git clone $CUR_BASE/${CUR_REPO} && cd ${CUR_REPO} && python setup.py install && cd .. && rm -rf ./${CUR_REPO}

CUR_INT="drill"
CUR_REPO="jupyter_${CUR_INT}"
echo ""
echo "$CUR_REPO"
echo ""
git clone $CUR_BASE/${CUR_REPO} && cd ${CUR_REPO} && python setup.py install && cd .. && rm -rf ./${CUR_REPO}

CUR_INT="pyodbc"
CUR_REPO="jupyter_${CUR_INT}"
echo ""
echo "$CUR_REPO"
echo ""
git clone $CUR_BASE/${CUR_REPO} && cd ${CUR_REPO} && python setup.py install && cd .. && rm -rf ./${CUR_REPO}

CUR_INT="impala"
CUR_REPO="jupyter_${CUR_INT}"
echo ""
echo "$CUR_REPO"
echo ""
git clone $CUR_BASE/${CUR_REPO} && cd ${CUR_REPO} && python setup.py install && cd .. && rm -rf ./${CUR_REPO}

CUR_INT="hive"
CUR_REPO="jupyter_${CUR_INT}"
echo ""
echo "$CUR_REPO"
echo ""
git clone $CUR_BASE/${CUR_REPO} && cd ${CUR_REPO} && python setup.py install && cd .. && rm -rf ./${CUR_REPO}

CUR_INT="es"
CUR_REPO="jupyter_${CUR_INT}"
echo ""
echo "$CUR_REPO"
echo ""
git clone $CUR_BASE/${CUR_REPO} && cd ${CUR_REPO} && python setup.py install && cd .. && rm -rf ./${CUR_REPO}

CUR_INT="mysql"
CUR_REPO="jupyter_${CUR_INT}"
echo ""
echo "$CUR_REPO"
echo ""
git clone $CUR_BASE/${CUR_REPO} && cd ${CUR_REPO} && python setup.py install && cd .. && rm -rf ./${CUR_REPO}



echo ""
echo "Checking for config locations"
echo ""

if [ ! -d "$HOME/.ipython/profile_default/startup" ]; then
    echo "Creating .ipython location for scripts"
    ipython profile create
else
    echo ".ipython profile location exists!"
fi

if [ ! -f "$HOME/.jupyter/jupyter_notebook_config.py" ]; then
    echo "Creating defualt jupyterlab config and updating iopub data rate"
    jupyter lab --generate-config
    sed -i '' "s/# c.NotebookApp.iopub_data_rate_limit = 1000000/c.NotebookApp.iopub_data_rate_limit = 100000000/g" $HOME/.jupyter/jupyter_notebook_config.py
else
    echo "Jupyterlab config exists - trying to update iopub"
    sed -i '' "s/# c.NotebookApp.iopub_data_rate_limit = 1000000/c.NotebookApp.iopub_data_rate_limit = 100000000/g" $HOME/.jupyter/jupyter_notebook_config.py
fi

SU="$HOME/.ipython/profile_default/startup/"

CUR="${SU}10_ipy.py"

if [ ! -f "${CUR}" ]; then
    echo "Creating $CUR"
    echo "ipy = get_ipython()" > ${CUR}
fi

CUR="${SU}11_drill.py"
if [ ! -f "${CUR}" ]; then
    echo "Creating $CUR"
    echo "from drill_core import Drill" > $CUR
    echo "myDrill = Drill(ipy, debug=False, pd_display_grid='qgrid')" >> $CUR
    echo "ipy.register_magics(myDrill)" >> $CUR
fi

CUR="${SU}12_splunk.py"
if [ ! -f "${CUR}" ]; then
    echo "Creating $CUR"
    echo "from splunk_core import Splunk" > $CUR
    echo "mySplunk = Splunk(ipy, debug=False, pd_display_grid='qgrid')" >> $CUR
    echo "ipy.register_magics(mySplunk)" >> $CUR
fi

CUR="${SU}13_mysql.py"
if [ ! -f "${CUR}" ]; then
    echo "Creating $CUR"
    echo "from mysql_core import Mysql" > $CUR
    echo "myMysql = Mysql(ipy, debug=False, pd_display_grid='qgrid')" >> $CUR
    echo "ipy.register_magics(myMysql)" >> $CUR
fi

CUR="${SU}14_impala.py"
if [ ! -f "${CUR}" ]; then
    echo "Creating $CUR"
    echo "from impala_core import Impala" > $CUR
    echo "myImpala = Impala(ipy, debug=False, pd_display_grid='qgrid')" >> $CUR
    echo "ipy.register_magics(myImpala)" >> $CUR
fi

CUR="${SU}15_hive.py"
if [ ! -f "${CUR}" ]; then
    echo "Creating $CUR"
    echo "from hive_core import Hive" > $CUR
    echo "myHive = Hive(ipy, debug=False, pd_display_grid='qgrid')" >> $CUR
    echo "ipy.register_magics(myHive)" >> $CUR
fi


CUR="${SU}16_es.py"
if [ ! -f "${CUR}" ]; then
    echo "Creating $CUR"
    echo "from es_core import Es" > $CUR
    echo "myEs = Es(ipy, debug=False, pd_display_grid='qgrid')" >> $CUR
    echo "ipy.register_magics(myEs)" >> $CUR
fi


echo ""
echo "Creating startup script  $HOME/${JUPENV}.sh"
echo ""

cat > $HOME/${JUPENV}.sh << EOF
#!/bin/bash

# Activate New Conda Env
source activate $JUPENV


# We try to load a file at $HOME/.jupyter_integration_data_sources
# This is a shell script just like this one, but allows for a shared list of data sources 

export JUPYTER_DISPLAY_PD_DISPLAY_GRID="qgrid"


. $HOME/.jupyter_integration_data_sources
# Example Drill
# The Instance name is embed
# And we set the Drill integration default to be embded
# export JUPYTER_DRILL_CONN_URL_EMBED="http://drill@localhost:8047?drill_embedded=1"
# export JUPYTER_DRILL_CONN_DEFAULT="embed"

# We included a Splunk connection - but it's commented out - Updated the User(splunkuser) and host (splunkhost) if you want to use 
# The splunk instance name is mainsplunk, and it's set to be the default
# I included a different example splunk instance named othersplunk.

# export JUPYTER_SPLUNK_CONN_URL_MAINSPLUNK="splunk://splunkuser@splunkhost:8089"
# export JUPYTER_SPLUNK_CONN_URL_OTHERSPLUNK="splunk://splunkuser@othersplunkhost:8089"
# export JUPYTER_SPLUNK_CONN_DEFAULT="mainsplunk"

# Here is an example mysql connection
# They are commented out, I provided two, intel and events. Uncomment, the exports and update as needed
# export JUPYTER_MYSQL_CONN_URL_INTEL="mysql://myuser@myintelhost:3306"
# export JUPYTER_MYSQL_CONN_URL_EVENTS="mysql://myuser@myeventhost:3306"
# export JUPYTER_MYSQL_CONN_DEFAULT="intel"

jupyter lab

EOF

chmod +x $HOME/${JUPENV}.sh 


unset CONDA_ALWAYS_YES
