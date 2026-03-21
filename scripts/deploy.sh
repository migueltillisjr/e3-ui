#!/bin/bash
# Deploy e3-ui to EC2, then pull and deploy e3 alongside it
set -euo pipefail

KEY="~/.ssh/11222024.pem"
IP="18.144.177.147"
SSH="ssh -i $KEY ubuntu@$IP"
SCP="scp -i $KEY"

# --- Deploy e3-ui ---
echo "=== Deploying e3-ui ==="

echo "Removing old e3-ui release..."
rm -f e3-ui-release.zip
$SSH "sudo rm -f /opt/e3-ui-release.zip"
$SSH "sudo rm -rf /opt/e3-ui"

echo "Creating new e3-ui release..."
git archive -o e3-ui-release.zip HEAD

echo "Uploading e3-ui release..."
$SCP e3-ui-release.zip ubuntu@$IP:/home/ubuntu/
$SSH "sudo mv /home/ubuntu/e3-ui-release.zip /opt/"

echo "Extracting e3-ui..."
$SSH "sudo mkdir -p /opt/e3-ui; sudo unzip -o /opt/e3-ui-release.zip -d /opt/e3-ui"

# --- Deploy e3 alongside ---
echo ""
echo "=== Deploying e3 alongside ==="

# Upload the deploy-e3.sh script and run it on the server
$SCP scripts/deploy-e3.sh ubuntu@$IP:/home/ubuntu/deploy-e3.sh
$SSH "chmod +x /home/ubuntu/deploy-e3.sh; /home/ubuntu/deploy-e3.sh"

echo ""
echo "=== Restarting service ==="
$SSH "sudo systemctl restart uvicorn.service"

echo ""
echo "=== Deploy complete ==="
