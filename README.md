# jupyter_integration_base - Base Package
-----
The Jupyter Integrations are a system of tools and base classes that allows folks to make connections to multiple data sources and use that data in a consistent way. 

Jupyter integrations proivide two main abstractions

- Integrations
  - Integrations are used to connect to a source of data and return it back as a Dataframe to the notebook
  - It handles connections, authentications, objects, error checking, query validation, help, and parsing of results.
  - It is a base class that can be extened and customized for every data source from DMBS, to ODBC, to API, to custom objects. 
- Addons
  - Addons are features that are included in the jupyter_integrations_base that help people work with their data.
  - Addons include helpers for displaying, visualizing, profiling, programmatically working with and manipulating your data. 


## Goals
-------
- Have a strong opinion of how Jupyter notebooks should interact with datasets
- Provide a base functions that will be reused by most data connections
- Allow data sets to incorporate custom objects/code to handle edge cases
- Allow users to interact with datasets in a very common way. 

## Philosphy
------
- Interactions with data stores should be as close to the native language, if not exactly the native language. 
- Data canbe retrieved with the native langauge and explored in a simple grid with NO Python knowledge
- All queries are also returned to a Pandas Dataframe ready to be used programatically as desired. 




## Environment Setup

- Conda
  - Please look in bootstrap/ for conda_bootstrap.sh
  - This should just work with Conda 3.8 or greater
- Pip 
  - Not yet created - TODO
- Docker
  - Not yet create - TODO



## Please see bootstrap folder for all the requirements

## Getting Started:
- When installed, please start via the script in ~/yourenvname.sh
- Please type %helloworld to start exploring. 


## Current Integrations
-------

Currently Working:
------
- jupyter_splunk 
  - https://github.com/johnomernik/jupyter_splunk
- jupyter_drill 
  - https://github.com/johnomernik/jupyter_drill
- jupyter_mysql
  - https://github.com/johnomernik/jupyter_mysql
- jupyter_es (Elastic Search)
  - https://githunb.com/johnomernik/juputer_es
- jupyter_pyodbc
  - https://github.com/johnomernik/jupyter_pyodbc
  - Parent Class to:
    - jupyter_impala
      - https://github.com/johnomernik/jupyter_impala
    - jupyter_tera
      - https://github.com/johnomernik/jupyter_tera

## Current Addons
-----------
- vis
  - A simple graphing interface using plotly
- profile
  - Profile your data with Pandas profiling
- persist
  - Save your dataframes in pickle files for opening in other notebooks, or later sessions
- display 
  - The add on for displaying in a grid and setting features.
- helloworld
  - A simple starting point to see what is loaded
- funcs
  - A shared function interface



## Opinionated Items
--------
- All integrations will use magic functions
  - Line magics (%) for interacting with the integration (connect, help, etc) 
  - Cell magics (%%) for submitting most queries. 
- Queries will be submited in the dataset's natural language, without quoting or "object handling"
  - Object handling is my term for all the code you have to write in order to submit a query
- Some integrations may use widgets due to a lack of common query langauge
- All data as the result of a query will be displayed on a grid without any interaction
- All data will be returned as Pandas Dataframe as well. 



