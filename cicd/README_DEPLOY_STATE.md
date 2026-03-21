# Deploy State Logging

The deployment scripts now log all deployment activities to `.deploy_state/` directory.

## Features

- Timestamped log files for each deployment
- Captures all deployment steps with timestamps
- Logs both stdout and stderr
- Preserves deployment history

## Log File Format

```
.deploy_state/<app>_<release>_<timestamp>.log
```

Example:
```
.deploy_state/hair_main_20260228_143022.log
```

## Usage

Just run your normal deployment:

```bash
cd cicd
./deploy.sh hair main
```

The script will automatically:
1. Create `.deploy_state/` directory if it doesn't exist
2. Create a timestamped log file
3. Log all deployment steps with timestamps
4. Display the log file path at the end

## Log Contents

Each log includes:
- Deployment start time and parameters
- Target group deployment output
- Networking deployment output  
- Code deployment steps:
  - Git clone
  - Python environment setup
  - Configuration file copies
  - SSL certificate deployment
  - Systemd service restart
- Completion timestamp

## Viewing Logs

```bash
# View latest deployment
ls -lt cicd/.deploy_state/ | head -n 1

# View specific deployment
cat cicd/.deploy_state/hair_main_20260228_143022.log

# Search for errors
grep -i error cicd/.deploy_state/*.log

# View all deployments for an app
ls cicd/.deploy_state/hair_*
```

## Make Scripts Executable

Before first use, make sure scripts are executable:

```bash
chmod +x cicd/deploy.sh
chmod +x cicd/tools/code_deploy.sh
```
