#!/usr/bin/env python
from __future__ import print_function

import os
import sys
import setuptools
v = sys.version_info
if v[:2] < (3, 3):
    error = "ERROR: Jupyter Hub requires Python version 3.3 or above."
    print(error, file=sys.stderr)
    sys.exit(1)


#if os.name in ('nt', 'dos'):
#    error = "ERROR: Windows is not supported"
#    print(error, file=sys.stderr)

# At least we're on the python version we need, move on.

from distutils.core import setup

pjoin = os.path.join
here = os.path.abspath(os.path.dirname(__file__))

# Get the current package version.
version_ns = {}

with open(pjoin(here,'integration_core', '_version.py')) as f:
    exec(f.read(), {}, version_ns)

#    packages=['integration_core', 'visualization_core', 'doc_core', 'profile_core', 'mymod'],

setup_args = dict(
    name='jupyter_integration_base',
    packages=setuptools.find_packages(),
    version=version_ns['__version__'],
    description="""An Interface Jupyter Notebooks.""",
    long_description="A core class for working with custom integrations for Python3 based Jupyter Notebooks",
    author="John Omernik",
    author_email="mandolinplayer@gmail.comm",
    url="https://github.com/JohnOmernik/jupyter_integration_base",
    license="Apache",
    platforms="Linux, Mac OS X",
    keywords=['Interactive', 'Interpreter', 'Shell', 'Notebook', 'Jupyter', "jupyter_integration_base"],
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Science/Research',
        'License :: Apache',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)

if 'bdist_wheel' in sys.argv:
    import setuptools

# setuptools requirements
if 'setuptools' in sys.modules:
    setup_args['install_requires'] = install_requires = []
    with open('requirements.txt') as f:
        for line in f.readlines():
            req = line.strip()
            if not req or req.startswith(('-e', '#')):
                continue
            install_requires.append(req)


def main():
    setup(**setup_args)

if __name__ == '__main__':
    main()
