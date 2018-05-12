#!/bin/bash

hugo

cd public
git add *
git commit -m "auto commit"
git push

cd ..
git add *
git commit -m "auto commit"
git push
