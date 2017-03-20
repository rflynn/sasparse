![build status](https://travis-ci.com/rflynn/sasparse.svg?token=ezxn8px7CJWy2JsCjEry&branch=master "Build Status")

# Run Me

    make test

# Parse SAS

## from stdin

    echo 'data _null_; put "Hello, World!"; run;' | venv/bin/python parse.py

## an arbitrary SAS file

    venv/bin/python parse.py path/to/file.sas

