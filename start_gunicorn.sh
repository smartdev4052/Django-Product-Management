#!/bin/bash

PATH_TO_VIRTUAL_ENV=/var/legisly/venv/bin

source $PATH_TO_VIRTUAL_ENV/activate

gunicorn core.wsgi --bind 127.0.0.1:5000 --timeout 30 --workers 3
