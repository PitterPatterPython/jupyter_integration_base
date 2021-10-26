cat > jupyter_integration_data_sources_template.env << EOF
# We try to load a file at $HOME/.jupyter_integration_data_sources
# This is a shell script just like this one, but allows for a shared list of data sources

JUPYTER_DISPLAY_PD_DISPLAY_GRID="qgrid"
JUPYTER_PERSIST_ADDON_DIR="/root/notebooks/persistdata"

JUPYTER_TAXII_CONN_URL_MITRE="https://cti-taxii.mitre.org:443?path=/taxii/&authreq=0"
JUPYTER_TAXII_CONN_DEFAULT="mitre"

# Example Drill
# The Instance name is embed
# And we set the Drill integration default to be embded
# JUPYTER_DRILL_CONN_URL_EMBED="http://drill@localhost:8047?drill_embedded=1"
# JUPYTER_DRILL_CONN_DEFAULT="embed"

# We included a Splunk connection - but it's commented out - Updated the User(splunkuser) and host (splunkhost) if you want to use 
# The splunk instance name is mainsplunk, and it's set to be the default
# I included a different example splunk instance named othersplunk.

# JUPYTER_SPLUNK_CONN_URL_MAINSPLUNK="splunk://splunkuser@splunkhost:8089"
# JUPYTER_SPLUNK_CONN_URL_OTHERSPLUNK="splunk://splunkuser@othersplunkhost:8089"
# JUPYTER_SPLUNK_CONN_DEFAULT="mainsplunk"

# Here is an example mysql connection
# They are commented out, I provided two, intel and events. Uncomment, the exports and update as needed
# JUPYTER_MYSQL_CONN_URL_INTEL="mysql://myuser@myintelhost:3306"
# JUPYTER_MYSQL_CONN_URL_EVENTS="mysql://myuser@myeventhost:3306"
# JUPYTER_MYSQL_CONN_DEFAULT="intel"

# Example Elastic Search
# JUPYTER_ES_CONN_URL_LOCAL="http://192.168.0.85:9200?no_auth=1"
# JUPYTER_ES_CONN_DEFAULT="local"


# Example Shared Function loaded as "mymod"
# JUPYTER_SHAREDFUNC_URL_MYMOD="mymod@https://raw.githubusercontent.com/JohnOmernik/sharedmod/main/mymod/_funcdocs.py"


EOF
