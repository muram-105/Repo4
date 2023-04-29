#!/bin/bash
git clone https://github.com/muram-105/Repo3.git
cd Repo3

git checkout main


git config --global user.email "muram8700@gmail.com"
git config --global user.name "muram-105"
git remote add Repo4 muram-105/Repo4

git fetch Repo4 main
git commit -m "add changes"

git merge Repo4/main
git push origin main

# cd ..
# rm -rf Repo3
