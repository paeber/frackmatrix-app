#!/bin/bash

cat << "EOF"
======================================================================
███████╗██████╗ ███████╗██████╗ ██╗    ██╗ █████╗ ██████╗ ███████╗
██╔════╝██╔══██╗██╔════╝██╔══██╗██║    ██║██╔══██╗██╔══██╗██╔════╝
█████╗  ██████╔╝█████╗  ██████╔╝██║ █╗ ██║███████║██████╔╝█████╗  
██╔══╝  ██╔══██╗██╔══╝  ██╔══██╗██║███╗██║██╔══██║██╔══██╗██╔══╝  
███████╗██████╔╝███████╗██║  ██║╚███╔███╔╝██║  ██║██║  ██║███████╗
╚══════╝╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝             
======================================================================
 Loader Version: 0.0.1
 Date: 2024-05-22
 Author: Pascal Eberhard
======================================================================
EOF

# Name of the branch to check
branch="main"

# Fetch updates from the remote repository
git fetch

# Compare the local and remote branches
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

if [ $LOCAL != $REMOTE ]; then
    echo "There are changes available to pull."

    # Show the commit message from the available pull
    echo "Commit message from the available pull:"
    git log --oneline $LOCAL..$REMOTE

    sleep 5

    # Pull the changes
    git pull origin $branch

    # Restart the script
    echo "Restarting the script..."
    sh $0

else
    echo "No changes available to pull."
    echo "Starting the application..."
    sleep 2
    venv/bin/python3 main.py
fi
