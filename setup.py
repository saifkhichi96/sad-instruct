""" Package setup.py """

import os

from setuptools import find_packages, setup

# Get the current directory
HERE = os.path.abspath(os.path.dirname(__file__))

# The name of the package
package='prompting'

# Get the long description from the README file
with open(os.path.join(HERE, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Load the requirements
with open(os.path.join(HERE, 'requirements.txt'), encoding='utf-8') as f:
    requirements = f.read().splitlines()

# Load the version
with open(os.path.join(HERE, package, 'VERSION'), encoding='utf-8') as f:
    version = f.read().strip()

setup(
    name=package,
    version=version,
    description='Language model prompting package',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='',
    author='Saif Khan',
    packages=find_packages(exclude=['tests']),
    install_requires=requirements,
    python_requires='>=3.8',
    include_package_data=True,
)
