#!/bin/bash

SU="$HOME/.ipython/profile_default/startup"
OBJ_VAL="(ipy, debug=False)"
FILE_NUM=10

# ????
CUR="${SU}/05_ipy.py"
echo "Creating $CUR"
echo "ipy = get_ipython()" > ${CUR}

CUR="${SU}/08_helloworldgo.py"
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
# ???

INTS=("helloworld" "drill" "splunk" "mysql" "impala" "hive" "tera" "es" "oracle" "pyodbc" "mssql" "dummy" "dtools" "mongo")

create_file() {
    local VAL=${1,,}
    local OUTFILE="${SU}/${FILE_NUM}_${VAL}.py"

    echo "Creating $OUTFILE"
    cat << EOF > $OUTFILE
from ${VAL}_core.${VAL}_full import ${VAL^}
${VAL}_full = ${VAL^}${OBJ_VAL}
ipy.register_magics(${VAL}_full)
EOF
    ((FILE_NUM+=1))
}

for INT in "${INTS[@]}"
do
    OUTFILE="${SU}/10_helloworld.py"
    create_file $INT
done
echo "Startup Files Created"

jupyter lab --allow-root --no-browser --ip=0.0.0.0 --port=8888