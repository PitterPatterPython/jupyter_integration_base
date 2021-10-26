#!/bin/bash

SU="$HOME/.ipython/profile_default/startup/"

OBJ_VAL="(ipy, debug=False)"

CUR="${SU}10_ipy.py"
echo "Creating $CUR"
echo "ipy = get_ipython()" > ${CUR}
# ---------------------------------------------------

CUR="${SU}11_drill.py"
echo "Creating $CUR"
echo "from drill_core import Drill" > $CUR
echo "myDrill = Drill${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(myDrill)" >> $CUR

CUR="${SU}12_splunk.py"
echo "Creating $CUR"
echo "from splunk_core import Splunk" > $CUR
echo "mySplunk = Splunk${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(mySplunk)" >> $CUR

CUR="${SU}13_mysql.py"
echo "Creating $CUR"
echo "from mysql_core import Mysql" > $CUR
echo "myMysql = Mysql${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(myMysql)" >> $CUR

CUR="${SU}14_impala.py"
echo "Creating $CUR"
echo "from impala_core import Impala" > $CUR
echo "myImpala = Impala${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(myImpala)" >> $CUR

CUR="${SU}15_hive.py"
echo "Creating $CUR"
echo "from hive_core import Hive" > $CUR
echo "myHive = Hive${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(myHive)" >> $CUR

CUR="${SU}16_tera.py"
echo "Creating $CUR"
echo "from tera_core import Tera" > $CUR
echo "myTera = Tera${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(myTera)" >> $CUR

CUR="${SU}17_es.py"
echo "Creating $CUR"
echo "from es_core import Es" > $CUR
echo "myEs = Es${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(myEs)" >> $CUR

CUR="${SU}18_taxii.py"
echo "Creating $CUR"
echo "from taxii_core import Taxii" > $CUR
echo "myTaxii = Taxii${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(myTaxii)" >> $CUR

CUR="${SU}19_oracle.py"
echo "Creating $CUR"
echo "from oracle_core import Oracle" > $CUR
echo "myOracle = Oracle${OBJ_VAL}" >> $CUR
echo "ipy.register_magics(myOracle)" >> $CUR

echo "Startup Files Complete"

echo "trying this"

echo "#!/bin/bash" > ${HOME}/start_jupyter.sh
echo  "cd /root && jupyter lab --allow-root --no-browser --ip=0.0.0.0 --port=8888" >> ${HOME}/start_jupyter.sh
chmod +x ${HOME}/start_jupyter.sh

