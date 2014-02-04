#!/bin/bash

ipython -i memdam/server/admin.py -- --wsgi=true --host=0.0.0.0 --db /home/cow/data/events/ --blobs=/home/cow/data/blobs/
