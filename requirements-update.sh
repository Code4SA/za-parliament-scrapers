#!/bin/sh -ex
#
# Update requirements files from Pipfile.lock

# Don't include '-e .' in the main requirements file: this breaks things.
pipenv lock --requirements | grep -vF '-e .' >requirements.txt
pipenv lock --requirements --dev >requirements-dev.txt
