#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.md').read()
history = open('HISTORY.md').read().replace('.. :changelog:', '')

setup(
    name='gunitop',
    version='0.1.0',
    description='top-like gunicorn monitoring utility.',
    long_description=readme + '\n\n' + history,
    author='Kirill Borisov',
    author_email='lensvol@gmail.com',
    url='https://github.com/lensvol/gunitop',
    packages=[
        'gunitop',
    ],
    package_dir={'gunitop': 'gunitop'},
    include_package_data=True,
    install_requires=[
        'psutil'
    ],
    license="MIT",
    zip_safe=False,
    keywords='gunitop gunicorn',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
    entry_points={
        'console_scripts': [
            'gunitop = gunitop.main:main',
        ]
    }
)
