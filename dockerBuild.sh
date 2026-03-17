#!/bin/bash

docker build -t e3 -f Dockerfile .
docker tag e3:latest 509499992346.dkr.ecr.us-west-1.amazonaws.com/uw1-infopioneer-e3
aws ecr get-login-password --region us-west-1 | docker login --username AWS --password-stdin 509499992346.dkr.ecr.us-west-1.amazonaws.com
docker push 509499992346.dkr.ecr.us-west-1.amazonaws.com/uw1-infopioneer-e3:latest
# ssh -i ~/.ssh/11222024.pem ubuntu@52.53.214.173 "cd /opt/e3-storage; rm -rf *; ./deploy-e3.sh"
# ssh -i ~/.ssh/11222024.pem ubuntu@52.53.214.173 "git clone git@github.com:migueltillisjr/e3.git"
# scp ./deploy-e3.sh
# cd /opt/;./deploy-e3.sh;