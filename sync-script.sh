#!/bin/bash
git clone https://github.com/muram-105/Repo3.git
cd Repo3
ls 

git checkout main


git config --global user.email "muram8700@gmail.com"
git config --global user.name "muram-105"
git remote add Repo4 https://github.com/muram-105/Repo4.git
git remote -v

git fetch origin main

git commit -a -m "commit message"
git merge origin/main
git push Repo4 main
# cd ..
# rm -rf Repo3
