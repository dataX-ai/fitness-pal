#!/bin/bash

# Check if Django can connect to the database
python manage.py check --database default || exit 1

# Check if there are any pending migrations
python manage.py showmigrations --list | grep -q "\[ \]" && exit 1 || exit 0 