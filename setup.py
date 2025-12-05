#!/usr/bin/env python3

"Setuptools params"

from setuptools import setup, find_packages

VERSION = '0.3'

modname = distname = 'lynette'

def readme():

    with open('README.md','r') as f:
        return f.read()

setup(
    name=distname,
    version=VERSION,
    description='Front-end compiler for pne.',
    author='Jinghui Jiang',
    # author_email='cedgar@ethz.ch',
    packages=find_packages(),
    # long_description=readme(),
    # entry_points={'console_scripts': ['p4run = p4utils.p4run:main']},
    include_package_data = True,
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python 3",
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Topic :: System :: Networking",
        ],
    # keywords='networking pne front-end',
    # license='GPLv2',
    python_requires='>=3.8',
    install_requires=[
        # 'googleapis-common-protos >= 1.52',
        # 'grpcio >= 1.17.2',
        # 'ipaddr',
        # 'ipaddress',
        # 'networkx',
        # 'p4runtime',
        # 'protobuf >= 3.6.1',
        # 'psutil',
        # 'scapy == 2.4.4',
        'lark',
        'setuptools',
        'pysnooper'
    ],
    extras_require={}
)
