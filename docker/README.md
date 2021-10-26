# Building and running Jupyter Integrations Docker
--------
- Install Docker 
- Pull (this)  the jupyter_integration_base repo
- Go to the ./docker folder under jupyter_integration_base
- Run 
  - `./build.sh psf`
- When done run
  - `./run.sh psf`
  - There is a file called jupyter_integrations.cfg
   - Open this set the path to a local folder that can be mapped into your container to save notebooks, this is a one time thing
  - If you want to run multiple, you can pass an optional local port (instead of the default 8888)
    - `./run.sh psf 8889`
- Once Jupter is running, copy the 127.0.01 link to your browser, and you are good to go

- Pick the container type (conda or stacks)
- Build the container with the choosen container type
  - `./build.sh psf`
  - Standard PSF Python is the only supported approach at this time. 
- When it's done, please open the start.sh file. It has two lines you may want to edit
  - NOTEBOOKDIR - This is the where your notebooks will be stored on your machine (not in the container) and is mounted to /root/Notebooks
  - ENV_FILE - This is where your datasources and other information about your env. Make sure this is your Home Dir
- run `./start.sh conda` or `./start.sh stacks`
  - Like before, we recommend stacks
- When it's started it will provide you with a link, you should be able to hit that in a browser. 


