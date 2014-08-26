#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='django-wham',
    packages=find_packages(exclude=['wham_project']),
    version='0.1.2',
    description='Rest APIs disguised as Django ORM Models',
    author='Michael Bylstra',
    author_email='mbylstra@gmail.com',
    url='https://github.com/mbylstra/django-wham',
    install_requires=['django', 'requests']
)