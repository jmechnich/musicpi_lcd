#!/bin/sh

find . -name '*.pyc' | xargs rm -f
find . -name '*~' | xargs rm -f

