#!/bin/bash
aws ecr get-login-password --region us-west-1 | docker login --username AWS --password-stdin 509499992346.dkr.ecr.us-west-1.amazonaws.com
cd /opt/e3-storage/
datetime=$(date +"%Y-%m-%d_%H-%M-%S")
mv backend/storage/database/crm.db "crm.db.${datetime}"
rm -rf e3/
git clone git@github.com:migueltillisjr/e3.git
mv e3/backend/ .
docker pull 509499992346.dkr.ecr.us-west-1.amazonaws.com/uw1-infopioneer-e3:latest
docker rm --force e3
docker run -d \
  --name e3 \
  -v /opt/e3-storage/backend:/app/backend \
  -p 443:443 \
  509499992346.dkr.ecr.us-west-1.amazonaws.com/uw1-infopioneer-e3