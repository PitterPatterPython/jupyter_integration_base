# Building and running Jupyter Integrations Docker
--------
The current setup works with a Python Software Foundation (psf) build. The most basic steps to get it working are from this directory:

- Install Docker (make sure it's installed)
- Edit jupyter_integrations.cfg 
   - Pick a local path to store notebooks - NOTEBOOKDIR
   - Pick a local file locationto store data sources - ENV_FILE
- `./build.sh psf`
- `./run.sh psf`
- Once it's running, Jupyter will provide links for you. Copy and Paste them to a browser. Use the 127.0.0.1 one!

## Multiple Instances
------
Since we use local port 8888, if you want to use a different port or run multiple instances, pass a port number to run command like this:

`./run.sh psf 8889`

This command will have Docker listen on 8889 instead of 8888. Note, the link from Jupyter will still show 8888 in the port, so that's a pain in the arse. I should maybe fix that. 

To get around this, just change the provided link port from 8888 to whatever you specified. 

## Other Types of Image
------
We have the ability to use other types of images other than the Python Software Foundation (psf) image, however, none are currently working. 

If you have a need for an anaconda one, or something, make an issue or hit me up. 


