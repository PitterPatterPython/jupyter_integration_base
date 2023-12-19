import os
import requests
import shutil
import subprocess
import sys
import zipfile

def install_integration(integration_name, repo_url, proxies):
    """Execute a subprocess to downlad a Python package from git (the zip file)
        and install it

    Args:
        integration_name (string): The name of the package we're going to install
        repo_url (_type_): The URL to the zip file in Git (or anywhere, else really)
        proxies (_type_): The user's "myproxies" environment variable

    Returns:
        output: The subprocess' output/results
    """
    requests.packages.urllib3.disable_warnings()
    
    response = requests.get(repo_url, proxies=proxies, verify=False)
    
    zip_content = response.content
    
    with open(f"{integration_name}.zip", "wb") as afile:
        afile.write(zip_content)
    
    with zipfile.ZipFile(f"{integration_name}.zip", "r") as afile:
        afile.extractall(integration_name)
    
    repo_source_dir = os.path.join(os.getcwd(), integration_name, os.listdir(integration_name)[0])
    output = subprocess.run(["pip", "install", "--upgrade", "--force-reinstall", "."], cwd=repo_source_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return output

def cleanup_install(integration_name):
    """Clean up the local files from our integration installation process

    Args:
        integration_name (string): The name of the integration to uninstall
    """
    if os.path.exists(f"{integration_name}.zip"):
        os.remove(f"{integration_name}.zip")
    if os.path.exists(integration_name):
        shutil.rmtree(integration_name)

def create_load_script(integration_name):
    """Create the string for the IPython startup script which can be loaded into
        the user's environment, or added as a startup script
    
    Args:
        integration_name (string): the name of the integration to create the startup script for

    Returns:
        string: the string representation of the startup script that the user can copy/paste
            into their environment or add to a startup script
    """
    load_script = (f"from {integration_name}_core.{integration_name}_base import {integration_name.capitalize()}\n"
                   f"{integration_name}_base = {integration_name.capitalize()}(ipy, debug=False)\n"
                   f"ipy.register_magics({integration_name}_base)\n")
    return load_script