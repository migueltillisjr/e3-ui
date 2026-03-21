#!/bin/bash
# Runs ON the server — clones e3 repo alongside e3-ui so it has access to e3 files
set -euo pipefail

echo "Deploying e3 alongside e3-ui..."

# Clean previous e3 clone
sudo rm -rf /opt/e3

# Clone fresh copy of e3
cd /opt
sudo git clone git@github.com:migueltillisjr/e3.git /opt/e3

echo "e3 deployed to /opt/e3"
echo "e3-ui at /opt/e3-ui can now access e3 files at /opt/e3"
