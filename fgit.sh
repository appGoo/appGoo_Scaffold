#!/bin/bash
#
# Usage: ./fgit.sh "commit message"
git add --all
git commit -m "$1"
git push

