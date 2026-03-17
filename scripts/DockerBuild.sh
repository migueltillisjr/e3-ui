#!/bin/bash
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 509499992346.dkr.ecr.us-west-2.amazonaws.com
docker build -t e3/e3w .
docker tag e3/e3w 509499992346.dkr.ecr.us-west-2.amazonaws.com/e3/e3w:latest
docker push 509499992346.dkr.ecr.us-west-2.amazonaws.com/e3/e3w:latest