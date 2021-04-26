# Building and running Jupyter Integrations Docker
--------
- Install Docker 
- Pick the container type (conda is the only only choice for now)
- Build the container with the choosen container type
  - `./build.sh conda` or `./build.sh stacks`
    - conda is my initial attempt at a container, it's slightly smaller and doesn't work as well. . 
    - stacks is a container based on the Jupyter Foundation's images. It's slightly larger, but it's better. Use this
- Current recommendation is stacks
- When it's done, please open the start.sh file. It has two lines you may want to edit
  - NOTEBOOKDIR - This is the where your notebooks will be stored on your machine (not in the container) and is mounted to /root/Notebooks
  - ENV_FILE - This is where your datasources and other information about your env. Make sure this is your Home Dir
- run `./start.sh conda` or `./start.sh stacks`
  - Like before, we recommend stacks
- When it's started it will provide you with a link, you should be able to hit that in a browser. 


