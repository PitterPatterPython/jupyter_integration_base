import os
import requests
import shutil
import subprocess
import sys
import zipfile

def uninstall_integration(repo_name):
    
    uninstall_process = subprocess.run(["pip", "uninstall", "-y", repo_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    uninstall_code = uninstall_process.returncode
    return uninstall_code


def install_integration(repo_name, repo_url, proxies):
    requests.packages.urllib3.disable_warnings()
    
    response = requests.get(repo_url, proxies=proxies, verify=False)
    
    zip_content = response.content
    
    with open(f"{repo_name}.zip", "wb") as afile:
        afile.write(zip_content)
    
    with zipfile.ZipFile(f"{repo_name}.zip", "r") as afile:
        afile.extractall(repo_name)
    
    repo_source_dir = os.path.join(os.getcwd(), repo_name, os.listdir(repo_name)[0])
    install_process = subprocess.run([sys.executable, "setup.py", "install", "--force"], cwd=repo_source_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    install_code = install_process.returncode
    
    return install_code

def cleanup_install(repo_name):
    if os.path.exists(f"{repo_name}.zip"):
        os.remove(f"{repo_name}.zip")
    if os.path.exists(repo_name):
        shutil.rmtree(repo_name)

def create_load_script(repo_name):
    load_script = (f"from {repo_name}_core.{repo_name}_base import {repo_name.capitalize()}\n"
                   f"{repo_name}_base = {repo_name.capitalize()}(ipy, debug=False)\n"
                   f"ipy.register_magics({repo_name}_base)\n")
    return load_script