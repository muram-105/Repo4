#!/bin/bash

# Clone the source repository
git clone https://github.com/muram-105/Repo3.git
cd Repo3

# Check out the source branch
git checkout source-branch

# Add a remote for the target repository
git remote add target-repo https://github.com/muram-105/Repo4.git

# Fetch the latest changes from the target branch of the target repository
git fetch Repo4 main

# Merge the changes from the target branch of the target repository into the source branch
git merge Repo4/main

# Push the changes to the source branch of the source repository
git push origin smain

# Clean up
cd ..
rm -rf Repo3
