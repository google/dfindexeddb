"""
Copyright 2024 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import glob
import os
import pkg_resources
from setuptools import find_packages
from setuptools import setup


def parse_requirements_from_file(path):
    """Parses requirements from a requirements file.

    Args:
      path (str): path to the requirements file.

    Yields:
      str: package resource requirement.
    """
    with open(path, "r") as file_object:
        file_contents = file_object.read()
    for req in pkg_resources.parse_requirements(file_contents):
        try:
            requirement = str(req.req)
        except AttributeError:
            requirement = str(req)
        yield requirement

description = 'dfindexeddb is an experimental Python tool for performing digital forensic analysis of indexeddb artifacts.'

long_description = (
    """dfindexeddb is an experimental Python tool for performing digital forensic analysis of indexeddb artifacts.

It parses leveldb, indexeddb and javascript structures without requiring native libraries.""")

setup(
    name='dfindexeddb',
    version='0.0.1',
    description=description,
    long_description=long_description,
    license='Apache License, Version 2.0',
    url='https://github.com/google/dfindexeddb',
    maintainer='Syd Pleno',
    maintainer_email='sydp@google.com',
    classifiers=[
        'Development Status :: 1 - Alpha',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    packages=find_packages('.', exclude=[
        'docs', 'test_data', 'tests', 'tests.*', 'tools']),
    scripts=glob.glob(os.path.join('tools', '[a-z_]*.py')),
    data_files=[
        ('share/doc/dfindexeddb', [
            'AUTHORS', 'LICENSE', 'README.md']),
    ],
    install_requires=parse_requirements_from_file('requirements.txt'),
    tests_require=parse_requirements_from_file('test_requirements.txt'),
)
