#!/bin/bash

virtualenv venv -p /usr/bin/python2
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
