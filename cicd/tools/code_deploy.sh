#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

app=${1:?Usage: ./code_deploy.sh <app> <release>}
release=${2:?Usage: ./code_deploy.sh <app> <release>}
server="deploy-web5.infopnr.com"
key="~/.ssh/11222024.pem"

# Determine repo and deploy paths based on app config
# e3 uses e3-ui repo deployed to /opt/e3-storage, web5 apps use web5.infopnr.com repo to /opt/web5
if [ -f "$app/$app.yaml" ]; then
  repo=$(grep '^repo:' "$app/$app.yaml" | awk '{print $2}' || echo "")
  deploy_base=$(grep '^deploy_base:' "$app/$app.yaml" | awk '{print $2}' || echo "")
  e3_repo=$(grep '^e3_repo:' "$app/$app.yaml" | awk '{print $2}' || echo "")
fi

# Defaults for web5-based apps
repo=${repo:-"migueltillisjr/web5.infopnr.com"}
deploy_base=${deploy_base:-"/opt/web5"}
repo_name=$(basename "$repo")

echo "🚀 Deploying release '$release' for app '$app'..."
echo "   Repo: $repo"
echo "   Deploy base: $deploy_base"

# Helper: run remote command safely
run_remote() {
  ssh -i "$key" -o StrictHostKeyChecking=accept-new ubuntu@"$server" "set -euo pipefail; $1"
}

# --- Step 1: Pull code from GitHub ---
echo "📦 Checking if code needs to be pulled..."
if run_remote "[ -d $deploy_base/$app/$repo_name/.git ]"; then
  echo "📦 Code directory exists, fetching latest changes..."
  run_remote "
    cd $deploy_base/$app/$repo_name
    git fetch --all --tags --force

    # Check if it's a tag or branch
    if git rev-parse 'refs/tags/$release' >/dev/null 2>&1; then
      echo 'Checking out tag: $release'
      git checkout 'tags/$release' -f
    elif git rev-parse 'origin/$release' >/dev/null 2>&1; then
      echo 'Checking out branch: $release'
      git checkout '$release' -f
      git reset --hard 'origin/$release'
    else
      echo 'Checking out ref: $release'
      git checkout '$release' -f
    fi
  "
else
  echo "📦 Cloning fresh repository..."
  run_remote "
    mkdir -p '$deploy_base/$app'
    cd '$deploy_base/$app'
    rm -rf '$repo_name'
    git clone --branch '$release' -- git@github.com:$repo.git || \
    (git clone -- git@github.com:$repo.git && \
     cd $repo_name && \
     git fetch --all --tags --force && \
     git checkout '$release' -f)
  "
fi

# --- Step 1b: Deploy e3 alongside (if e3_repo is configured) ---
if [ -n "${e3_repo:-}" ]; then
  e3_repo_name=$(basename "$e3_repo")
  echo ""
  echo "📦 Deploying $e3_repo_name alongside $app..."
  if run_remote "[ -d $deploy_base/$e3_repo_name/.git ]"; then
    echo "📦 e3 repo exists, pulling latest..."
    run_remote "
      cd $deploy_base/$e3_repo_name
      git fetch --all --tags --force
      git checkout main -f
      git reset --hard origin/main
    "
  else
    echo "📦 Cloning e3 repo..."
    run_remote "
      cd $deploy_base
      rm -rf '$e3_repo_name'
      git clone -- git@github.com:$e3_repo.git
    "
  fi
  echo "✅ e3 deployed to $deploy_base/$e3_repo_name"
fi

# --- Step 2: Install dependencies ---
echo ""
echo "📦 Setting up Python environment..."
run_remote "
  cd $deploy_base/$app/$repo_name
  if [ ! -d .$app ]; then
    echo 'Creating new virtual environment...'
    /usr/local/bin/python3.13 -m venv .$app
  else
    echo 'Virtual environment already exists'
  fi
  source .$app/bin/activate
  pip install --no-cache-dir -r requirements.txt
"

# --- Step 3: Copy .env file ---
echo "📄 Copying .env..."
scp -i "$key" -o StrictHostKeyChecking=accept-new "cicd/$app/env" "ubuntu@$server:$deploy_base/$app/$repo_name/.env"
# Update .env file with the new app route prefix path
ssh -i "$key" ubuntu@$server "
  sed -i \
    -e \"s|SERVER_ROUTE_PREFIX=\\\"[^\\\"]*\\\"|SERVER_ROUTE_PREFIX=\\\"/$app\\\"|\" \
    -e \"s|CLIENT_ROUTE_PREFIX=\\\"[^\\\"]*\\\"|CLIENT_ROUTE_PREFIX=\\\"/$app\\\"|\" \
    $deploy_base/$app/$repo_name/.env
"

echo "📄 Copying js global config..."
scp -i "$key" -o StrictHostKeyChecking=accept-new "cicd/$app/global.js" "ubuntu@$server:$deploy_base/$app/$repo_name/frontend/js/global.js"

echo '🔒 Copying certs...'
for cert in fullchain.pem server.crt private.server.key; do
  if [ -f "../backend/security/$cert" ]; then
    scp -i "$key" -o StrictHostKeyChecking=accept-new "../backend/security/$cert" "ubuntu@$server:$deploy_base/$app/$repo_name/backend/security/"
  else
    echo "   ⚠️  Skipping $cert (not found locally)"
  fi
done

echo '⚙️ Deploying systemd service...'
if [ -f "cicd/$app/$app.service" ]; then
  # Use pre-built service file if it exists (e.g. e3 with custom paths)
  echo "Using pre-built service file: cicd/$app/$app.service"
  scp -i "$key" -o StrictHostKeyChecking=accept-new "cicd/$app/$app.service" "ubuntu@$server:/home/ubuntu/$app.service"
else
  # Generate from template for web5-based apps
  cp "tools/sample.service" "$app/$app.service"
  ./tools/update_service_file.py "$app/$app.yaml" "$app/$app.service"
  scp -i "$key" -o StrictHostKeyChecking=accept-new "$app/$app.service" "ubuntu@$server:/home/ubuntu/$app.service"
fi

# Check if service is already running and only restart if needed
SERVICE_STATUS=$(run_remote "systemctl is-active $app.service || echo inactive")
echo "Service status: $SERVICE_STATUS"

run_remote "
  sudo cp /home/ubuntu/$app.service /etc/systemd/system/$app.service
  sudo systemctl daemon-reload
  sudo systemctl enable $app.service

  if systemctl is-active --quiet $app.service; then
    echo 'Service is running, restarting...'
    sudo systemctl restart $app.service
  else
    echo 'Service is not running, starting...'
    sudo systemctl start $app.service
  fi

  # Wait a moment and check status
  sleep 2
  sudo systemctl status $app.service --no-pager || true
"

echo "✅ Successfully deployed '$app' release '$release'."
