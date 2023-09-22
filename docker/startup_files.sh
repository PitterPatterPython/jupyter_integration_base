#!/bin/bash

SU="$HOME/.ipython/profile_default/startup/"

OBJ_VAL="(ipy, debug=False)"

#
CUR="${SU}05_ipy.py"
echo "Creating $CUR"
echo "ipy = get_ipython()" > ${CUR}
# ---------------------------------------------------

CUR="${SU}08_helloworldgo.py"
echo "Creating $CUR"
echo "hello_go = r\"\"\"import datetime" > $CUR
echo "import pandas as pd" >> $CUR
echo "%run -i /root/Notebooks/shared_function_template.py" >> $CUR
echo "%splunk instances" >> $CUR
echo "\"\"\"" >> $CUR
echo "" >> $CUR
echo "hello_other = r\"\"\"import sys" >> $CUR
echo "print('Other Helloworld')" >> $CUR
echo "\"\"\"" >> $CUR


CUR="${SU}10_helloworld.py"
echo "Creating $CUR"
echo "from helloworld_core.helloworld_full import Helloworld" > $CUR
echo "helloworld_full = Helloworld${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(helloworld_full)" >> $CUR

CUR="${SU}11_drill.py"
echo "Creating $CUR"
echo "from drill_core.drill_base import Drill" > $CUR
echo "drill_base = Drill${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(drill_base)" >> $CUR

CUR="${SU}12_splunk.py"
echo "Creating $CUR"
echo "from splunk_core.splunk_base import Splunk" > $CUR
echo "splunk_base = Splunk${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(splunk_base)" >> $CUR

CUR="${SU}13_mysql.py"
echo "Creating $CUR"
echo "from mysql_core.mysql_base import Mysql" > $CUR
echo "mysql_base = Mysql${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(mysql_base)" >> $CUR

CUR="${SU}14_impala.py"
echo "Creating $CUR"
echo "from impala_core.impala_base import Impala" > $CUR
echo "impala_base = Impala${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(impala_base)" >> $CUR

CUR="${SU}15_hive.py"
echo "Creating $CUR"
echo "from hive_core.hive_base import Hive" > $CUR
echo "hive_base = Hive${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(hive_base)" >> $CUR

CUR="${SU}16_tera.py"
echo "Creating $CUR"
echo "from tera_core.tera_base import Tera" > $CUR
echo "tera_base = Tera${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(tera_base)" >> $CUR

CUR="${SU}17_es.py"
echo "Creating $CUR"
echo "from es_core.es_base import Es" > $CUR
echo "es_base = Es${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(es_base)" >> $CUR

CUR="${SU}18_taxii.py"
echo "Creating $CUR"
echo "from taxii_core.taxii_base import Taxii" > $CUR
echo "taxii_base = Taxii${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(taxii_base)" >> $CUR

CUR="${SU}19_oracle.py"
echo "Creating $CUR"
echo "from oracle_core.oracle_base import Oracle" > $CUR
echo "oracle_base = Oracle${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(oracle_base)" >> $CUR

CUR="${SU}20_pyodbc.py"
echo "Creating $CUR"
echo "from pyodbc_core.pyodbc_base import Pyodbc" > $CUR
echo "pyodbc_base = Pyodbc${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(pyodbc_base)" >> $CUR

CUR="${SU}21_mssql.py"
echo "Creating $CUR"
echo "from mssql_core.mssql_base import Mssql" > $CUR
echo "mssql_base = Mssql${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(mssql_base)" >> $CUR

CUR="${SU}22_dummy.py"
echo "Creating $CUR"
echo "from dummy_core.dummy_base import Dummy" > $CUR
echo "dummy_base = Dummy${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(dummy_base)" >> $CUR

CUR="${SU}23_dtools.py"
echo "Creating $CUR"
echo "from dtools_core.dtools_base import Dtools" > $CUR
echo "dtools_base = Dtools${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(dtools_base)" >> $CUR

CUR="${SU}24_urlscan.py"
echo "Creating $CUR"
echo "from urlscan_core.urlscan_base import Urlscan" > $CUR
echo "urlscan_base = Urlscan${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(urlscan_base)" >> $CUR

CUR="${SU}25_mongo.py"
echo "Creating $CUR"
echo "from mongo_core.mongo_base import Mongo" > $CUR
echo "mongo_base = Mongo${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(mongo_base)" >> $CUR



echo "Startup Files Complete"


echo "#!/bin/bash" > ${HOME}/start_jupyter.sh
echo  "cd /root && jupyter lab --allow-root --no-browser --ip=0.0.0.0 --port=8888" >> ${HOME}/start_jupyter.sh
chmod +x ${HOME}/start_jupyter.sh

