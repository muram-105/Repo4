#!/bin/bash
git clone https://github.com/muram-105/Repo3.git
cd Repo3

git checkout main

git remote add Repo4 https://github.com/muram-105/Repo4.git

git fetch Repo4 main
git commit -m "add changes"

# git merge Repo4/main

# git push origin main

# cd ..
# rm -rf Repo3
