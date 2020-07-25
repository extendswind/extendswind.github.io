#!/bin/bash


./myNote/ln2posts.sh

# compile markdown
hugo

# commit html file to github
cd public
git add .
git commit -m "auto commit"
git push  # 向github page的push
# git push coding master # 向coding net的push

# commit origin source to github
cd ..
git add .
git commit -m "auto commit"
git push

