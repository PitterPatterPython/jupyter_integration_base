# Installing Jupyter Integrations for the first time
----------------
Jupyter integrations is knowlingly complex.  The purpose is to handle many things for the analyst or data science, to make their day to day intuitive. 

This unfortunately results it the development and first time install of Jupyter Integrations being more complex. 

## Docker - Easy Choice
---------
To create a docker container you can run locally, the best way is to head here:

[Docker Bootstrapa] (docker/README.md)

We currently have a Python Software Foundation (psf) image working well with Jupyter Integrations. Please see the Docker README for other image times. 

## Manual Bootstrap - Harder Choice
---------
You may want to bootstrap this to your own specifications.  Like previously mentioned it's complex. I have included some files to help 


#### 1. Pre-Install Requirements
------

- All platforms
  - Python 3.9 or higher (PSF, Conda, etc)
  - Recommendation: Use Conda ENV or VENV in PSF, or use Docker containers!
- Windows
  - Microsoft Build Tools (2017 is tested)
  - Prior to going to step 2, please install wheel via pip
    - `pip install wheel`
  
- Linux
  - PyODBC Install process - Note ODBC note yet tested in Docker - this is something on the plan - Here is the PyODBC install from the psf Docker
 ```
apt-get update \
 && apt-get install --reinstall build-essential -y \
 && apt-get install unixodbc -y \
 && apt-get install unixodbc-dev -y \
 && apt-get install freetds-dev -y \
 && apt-get install freetds-bin -y \
 && apt-get install tdsodbc -y \
 && apt-get install --reinstall build-essential -y \
 && apt-get autoremove -y \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

echo "[FreeTDS]\n\
Description = FreeTDS unixODBC Driver\n\
Driver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so\n\
Setup = /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so" >> /etc/odbcinst.ini


pip install --trusted-host pypi.python.org pyodbc==4.0.30
```

#### 2. Initial Packages
-----
Once you have the intial packages installed, now you run the requirements. 

The working requirements will be in a file called current_requirements.txt.  This is a pip compatible requirements file.  For pip, you should be able to do:

`pip install -r current_requirements.txt`


This will work, but it is a very strict file, and may cause issues.  In the docker folder, there is a less stringent requirements file, try using that too. 




If you want to have "terminal" support in Windows, we've found that these goofy steps must be taken:

- `pip install pipwin`
- `pip uninstall --yes wheel`
- `pip install wheel`
- `pip uninstall --yes pywinpty`
- `pip install pywinpty`

This will allow you use to terminals in your Jupyter Lab 


#### 3. Create Jupyter/IPython configs
-------
Many of these steps can be seen in the Dockerfile_jupyter_integrations file under the docker folder


- `ipython profile create`
- `jupyter lab --generate-config`

Then in linux you can simply run this:
- `sed -i "s/# c.ServerApp.iopub_data_rate_limit = 1000000/c.ServerApp.iopub_data_rate_limit = 100000000/g" $HOME/.jupyter/jupyter_lab_config.py`

However, in Windows, you will need to go to your home directory, then to the file .jupyter\jupyter_lab_config.py

Open this in a text editor, find the line wiht c.ServerApp.iopub_data_rate_limit, uncomment the line (remove the #) and add two 0s :) 

 
#### 4. Install all the Jupyter Integration Packages
-------
The next step is easier if you are in linux because the commands should just run. In Windows, you will have to obtain each package, and in the env you've created install each of these. 

The list is in the docker/Dockerfile_jupyter_integrations file.  Basically take all the lines that start with RUN git clone and remove the run and run them. In Linux, it should work as is as long as you are in the correct env

This includes the qgrid one. 

#### 5. Jupyter Startup files
-------
This next part is harder if you are on windows and can't read BASH.  You essentially need to do what docker\startup_files.sh does. 

English Summary:
- It goes to the folder $HOME\.ipython\profile_default\startup
- It creates a file for each integration, but starts with 10_ipy.py to ensure the ipy variable is available to each

10_ipy.py
```ipy = get_ipython()```

Example 11_drill.py file
```from drill_core import Drill
myDrill = Drill(ipy, debug=False)
ipy.register_magics(myDrill)```

- These all exist in this startup directory so they are started as integrations are started

We could probably clean this up. Someday!

#### 5. Creating a Datasource file
-----
Once you get everything setup, you will want to create a persisted data sources file. Essentially, we recommend using a template:

Linux: docker\jupyter_integration_data_sources_template.env
Windows: docker\jupyter_integration_data_sources_templace.win

Copy this file to home directory location, 

NIX

`cp docker/jupyter_integration_data_sources_template.env $HOME/jupyter_integration_data_sources.env`

Windows

`copy docker\jupyter_integration_data_sources_templace.win %USERPROFILE%\jupyter_integration_data_sources.win`

Once the file is copied, you can edit the copied file and put your datasources in. 


#### 6. Starting Jupyterlab
-----

Once all of this is done, we start Jupyter lab. the startup_files.sh creates a bash script in the docker container, but here are the steps

1. Switch to the proper env
2. Import your datasources files from step 5
3. Run Jupyter lab

Example bash script in a nix env:
```
myenv/Scripts/activate
source $HOME/jupyter_integration_data_sources.env
jupyter lab --allow-root --no-browser --ip=0.0.0.0 --port=8888
```

Example bat file in Windows env:
```
call myenv\Scripts\activate.bat
call %USERPROFILE%\jupyter_integration_data_sources.win
jupyter lab --allow-root --no-browser --ip=0.0.0.0 --port=8888
```

You can remove the --allow-root and --no-browser if you'd like. 

This ugly process makes it so you can easily work in the environment after it's created
