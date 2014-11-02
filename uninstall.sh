#!/bin/sh

FILES=files.txt

echo "Deleting"
cat $FILES
cat $FILES | sudo xargs rm -rf
