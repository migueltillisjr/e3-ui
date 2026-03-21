#!/usr/bin/env python3
import sys
import time
import argparse
from typing import Any, Dict, Optional, List
import boto3
from botocore.exceptions import ClientError

try:
    import yaml  # pip install pyyaml
except Exception:
    yaml = None

"""
Adds automatic target registration and YAML config support:
- If --config is provided, reads required inputs from YAML.
- Interactive prompts are still used for any missing values unless --non-interactive is set.
- If 'targets' are provided in YAML, registration happens automatically without prompts.

Prereqs:
- pip install boto3 pyyaml
- AWS credentials configured (env vars, ~/.aws/credentials, or instance role)

Permissions needed (minimum):
- elasticloadbalancing:DescribeLoadBalancers
- elasticloadbalancing:DescribeListeners
- elasticloadbalancing:DescribeRules
- elasticloadbalancing:DescribeTargetGroups
- elasticloadbalancing:CreateTargetGroup
- elasticloadbalancing:RegisterTargets
- elasticloadbalancing:DescribeTargetHealth
- elasticloadbalancing:CreateRule
"""

# ---------------------- Helpers: ELBv2 describe/etc ----------------------
def pick_listener_by_port(elbv2, lb_arn: str, port: int):
    paginator = elbv2.get_paginator("describe_listeners")
    for page in paginator.paginate(LoadBalancerArn=lb_arn):
        for l in page.get("Listeners", []):
            if l.get("Port") == port:
                return l
    return None

def describe_target_group_by_name(elbv2, tg_name: str):
    paginator = elbv2.get_paginator("describe_target_groups")
    for page in paginator.paginate(Names=[tg_name]):
        tgs = page.get("TargetGroups", [])
        if tgs:
            return tgs[0]
    return None

def list_rules_for_listener(elbv2, listener_arn: str):
    rules = []
    paginator = elbv2.get_paginator("describe_rules")
    for page in paginator.paginate(ListenerArn=listener_arn):
        rules.extend(page.get("Rules", []))
    return rules

def extract_path_patterns(rule):
    pats = []
    for cond in rule.get("Conditions", []):
        if cond.get("Field") == "path-pattern":
            cfg = cond.get("PathPatternConfig", {})
            pats.extend(cfg.get("Values", []))
    return pats

def extract_host_values(rule):
    hosts = []
    for cond in rule.get("Conditions", []):
        if cond.get("Field") == "host-header":
            cfg = cond.get("HostHeaderConfig", {})
            hosts.extend(cfg.get("Values", []))
    return hosts

def rule_targets(rule):
    tgs = []
    for act in rule.get("Actions", []):
        if act.get("Type") == "forward":
            cfg = act.get("ForwardConfig")
            if cfg and "TargetGroups" in cfg:
                tgs.extend([tg["TargetGroupArn"] for tg in cfg["TargetGroups"]])
            elif "TargetGroupArn" in act:
                tgs.append(act["TargetGroupArn"])
    return tgs

def next_free_priority(rules):
    used = set()
    for r in rules:
        p = r.get("Priority")
        if p and p.isdigit():
            used.add(int(p))
    p = 10
    while p in used:
        p += 10
    return p

# ---------------------- YAML + Input Handling ----------------------
class Config:
    def __init__(self, data: Optional[Dict[str, Any]] = None, non_interactive: bool = False):
        self.data = data or {}
        self.non_interactive = non_interactive

    def _need(self, key: str, prompt: str, default: Optional[str] = None, cast=None):
        # 1) YAML value
        if key in self.data and self.data[key] is not None:
            val = self.data[key]
            try:
                return cast(val) if cast else val
            except Exception:
                raise ValueError(f"Invalid value for '{key}': {val}")

        # 2) Default (non-interactive)
        if self.non_interactive:
            if default is not None:
                try:
                    return cast(default) if cast else default
                except Exception:
                    raise
            raise ValueError(f"Missing required '{key}' and non-interactive mode is enabled.")

        # 3) Interactive prompt
        txt = input(f"{prompt} ").strip()
        if not txt and default is not None:
            txt = str(default)
        if cast:
            try:
                return cast(txt)
            except Exception:
                raise ValueError(f"Invalid value for '{key}': {txt}")
        return txt

    def get(self, key: str, prompt: str, default: Optional[str] = None, cast=None):
        # Optional helper (allows empty)
        if key in self.data and self.data[key] is not None:
            val = self.data[key]
            return cast(val) if cast else val

        if self.non_interactive:
            if default is None:
                return None
            return cast(default) if cast else default

        txt = input(f"{prompt} ").strip()
        if not txt and default is not None:
            txt = str(default)
        if not txt and default is None:
            return None
        return cast(txt) if cast else txt

def load_yaml(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    if yaml is None:
        print("PyYAML is not installed. Install with: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"Config file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Failed to read YAML: {e}", file=sys.stderr)
        sys.exit(1)

# ---------------------- Target Registration ----------------------
def register_targets(elbv2, tg_arn: str, target_type: str, port: int, cfg: Config):
    """
    Registers targets either from YAML (preferred) or via interactive prompts.
    YAML shape:
      targets:
        availability_zone: us-west-1a   # optional
        instance_ids: [i-..., i-...]    # for target_type=instance
        ips: [10.0.1.10, 10.0.2.15]     # for target_type=ip
    """
    targets_cfg = cfg.data.get("targets") if isinstance(cfg.data, dict) else None

    # If the YAML provides targets, use them and skip prompting
    if isinstance(targets_cfg, dict):
        az_opt = targets_cfg.get("availability_zone", "").strip() or None
        targets = []

        if target_type == "instance":
            ids = targets_cfg.get("instance_ids") or []
            ids = [str(x).strip() for x in ids if str(x).strip()]
            if not ids and cfg.non_interactive:
                raise ValueError("targets.instance_ids is required for instance target_type in non-interactive mode.")
            for iid in ids:
                t = {"Id": iid}
                if az_opt:
                    t["AvailabilityZone"] = az_opt
                targets.append(t)

        elif target_type == "ip":
            ips = targets_cfg.get("ips") or []
            ips = [str(x).strip() for x in ips if str(x).strip()]
            if not ips and cfg.non_interactive:
                raise ValueError("targets.ips is required for ip target_type in non-interactive mode.")
            for ip in ips:
                t = {"Id": ip, "Port": port}
                if az_opt:
                    t["AvailabilityZone"] = az_opt
                targets.append(t)

        if targets:
            print(f"\nRegistering {len(targets)} target(s) from YAML to TG {tg_arn} ...")
            elbv2.register_targets(TargetGroupArn=tg_arn, Targets=targets)
            print("✅ Targets registered (from YAML).")
            return

        # If YAML block present but empty and interactive allowed, fall through to prompts
        print("No targets provided in YAML; switching to interactive registration...")

    # Interactive fallback
    targets = []
    if target_type == "instance":
        ids = cfg.get("instance_ids_prompt", "EC2 Instance IDs to register (comma-separated, e.g., i-abc,i-def):")
        if not ids:
            print("No instance IDs entered; skipping registration.")
            return
        az_opt = cfg.get("az_prompt", "Optional Availability Zone for *all* instances (e.g., us-west-1a) or leave blank:") or ""
        for iid in [x.strip() for x in ids.split(",") if x.strip()]:
            t = {"Id": iid}
            if az_opt:
                t["AvailabilityZone"] = az_opt
            targets.append(t)

    elif target_type == "ip":
        ips = cfg.get("ips_prompt", "IP addresses to register (comma-separated, e.g., 10.0.1.10,10.0.2.15):")
        if not ips:
            print("No IPs entered; skipping registration.")
            return
        az_opt = cfg.get("az_prompt", "Optional Availability Zone for *all* IPs (or leave blank):") or ""
        for ip in [x.strip() for x in ips.split(",") if x.strip()]:
            t = {"Id": ip, "Port": port}  # port required for IP targets
            if az_opt:
                t["AvailabilityZone"] = az_opt
            targets.append(t)
    else:
        print("Target registration skipped (unsupported target type for manual input).")
        return

    if targets:
        print(f"\nRegistering {len(targets)} target(s) to TG {tg_arn} ...")
        elbv2.register_targets(TargetGroupArn=tg_arn, Targets=targets)
        print("✅ Targets registered.")

def print_target_health(elbv2, tg_arn: str):
    try:
        resp = elbv2.describe_target_health(TargetGroupArn=tg_arn)
    except ClientError as e:
        print(f"describe_target_health failed: {e}", file=sys.stderr)
        return
    desc = resp.get("TargetHealthDescriptions", [])
    if not desc:
        print("No targets registered yet.")
        return
    print("\n=== Target Health ===")
    for d in desc:
        tgt = d.get("Target", {})
        th = d.get("TargetHealth", {})
        print(f"- {tgt.get('Id')} (port {tgt.get('Port')}) : {th.get('State')} - {th.get('Description')}")

# ---------------------- Main ----------------------
def main():
    ap = argparse.ArgumentParser(description="Create ALB rule + Target Group and (optionally) register targets. Supports YAML config.")
    ap.add_argument("-c", "--config", help="Path to YAML config file", default=None)
    ap.add_argument("--non-interactive", action="store_true", help="Fail if required values are missing instead of prompting")
    args = ap.parse_args()

    data = load_yaml(args.config)
    cfg = Config(data, non_interactive=args.non_interactive)

    # Collect inputs (YAML -> default -> prompt)
    region = cfg._need("region", "AWS region (e.g., us-west-1):", default="us-west-1", cast=str)
    lb_arn = cfg._need("lb_arn", "ALB ARN:", cast=str)
    tg_name_to_list = cfg._need("existing_tg_name", "Existing Target Group NAME to inspect (list rules that forward to it):", cast=str)

    try:
        elbv2 = boto3.client("elbv2", region_name=region)
    except Exception as e:
        print(f"Failed to init boto3 elbv2 client: {e}", file=sys.stderr)
        sys.exit(1)

    # Resolve the TG by name for listing
    try:
        tg = describe_target_group_by_name(elbv2, tg_name_to_list)
    except ClientError as e:
        if e.response["Error"]["Code"] == "TargetGroupNotFound":
            tg = None
        else:
            raise

    if not tg:
        print(f"Target Group '{tg_name_to_list}' not found in {region}.", file=sys.stderr)
        sys.exit(1)

    tg_arn = tg["TargetGroupArn"]

    listener_port = cfg._need("listener_port", "Listener port to inspect (e.g., 443):", default="443", cast=int)

    listener = pick_listener_by_port(elbv2, lb_arn, listener_port)
    if not listener:
        print(f"No listener found on port {listener_port} for ALB.", file=sys.stderr)
        sys.exit(1)

    print("\n=== Current rules that forward to the specified Target Group ===")
    rules = list_rules_for_listener(elbv2, listener["ListenerArn"])
    found_any = False
    for r in rules:
        tg_arns = rule_targets(r)
        if tg_arn in tg_arns:
            found_any = True
            paths = extract_path_patterns(r) or ["<no path condition>"]
            hosts = extract_host_values(r) or ["<any host>"]
            print(f"- Priority: {r.get('Priority')}")
            print(f"  Hosts: {', '.join(hosts)}")
            print(f"  Paths: {', '.join(paths)}")
            print(f"  Listener Port: {listener_port}")
            print(f"  Forwards to TG: {tg_name_to_list}")
    if not found_any:
        print("(none)")

    # If YAML defines new objects, skip pause. Otherwise allow interactive pause.
    if not args.non_interactive and "new_path" not in cfg.data:
        input("\nPress Enter to add a NEW context path + target group...")

    # Collect inputs for new TG + rule
    new_path = cfg._need("new_path", "New context path pattern (e.g., /web6*):", cast=str)
    new_host = cfg.get("new_host", "Optional host condition (e.g., web5.infopnr.com) or leave blank for any host:", default="", cast=str) or None
    new_tg_name = cfg._need("new_tg_name", "New Target Group NAME to create (e.g., tg-web6-8443):", cast=str)
    vpc_id = cfg._need("vpc_id", "VPC ID for the new Target Group (e.g., vpc-xxxxxxxx):", cast=str)

    target_protocol = cfg._need("target_protocol", "Target protocol [HTTP|HTTPS] (default HTTP):", default="HTTP", cast=lambda s: str(s).upper())
    if target_protocol not in ("HTTP", "HTTPS"):
        print("Target protocol must be HTTP or HTTPS.", file=sys.stderr)
        sys.exit(1)

    target_port = cfg._need("target_port", "Target port (e.g., 8443):", cast=int)

    health_path = cfg.get("health_path", "Health check path (default /health):", default="/health", cast=str)
    matcher = cfg.get("matcher", "Health check success codes (default 200-399):", default="200-399", cast=str)
    target_type = cfg._need("target_type", "Target type [instance|ip] (default instance):", default="instance", cast=lambda s: str(s).lower())
    if target_type not in ("instance", "ip"):
        print("Target type must be 'instance' or 'ip'.", file=sys.stderr)
        sys.exit(1)

    # Create (or reuse) the target group
    try:
        existing = describe_target_group_by_name(elbv2, new_tg_name)
    except ClientError as e:
        if e.response["Error"]["Code"] == "TargetGroupNotFound":
            existing = None
        else:
            raise

    if existing:
        existing_port = existing.get("Port")
        existing_protocol = existing.get("Protocol")
        
        # Check if configuration matches
        config_changed = (
            existing_port != target_port or 
            existing_protocol != target_protocol
        )
        
        if config_changed:
            print(f"\n⚠️  Existing Target Group '{new_tg_name}' has different configuration:")
            print(f"   Current: {existing_protocol}:{existing_port}")
            print(f"   Desired: {target_protocol}:{target_port}")
            print(f"\n🔄 Force deleting and recreating target group with new configuration...")
            
            try:
                # First, find and remove all listener rules that reference this target group
                print("🔍 Finding listener rules that reference this target group...")
                listener = pick_listener_by_port(elbv2, lb_arn, listener_port)
                if listener:
                    rules = list_rules_for_listener(elbv2, listener["ListenerArn"])
                    rules_to_delete = []
                    
                    for rule in rules:
                        if rule.get("Priority") == "default":
                            continue  # Skip default rule
                        tg_arns = rule_targets(rule)
                        if existing['TargetGroupArn'] in tg_arns:
                            rules_to_delete.append(rule)
                    
                    if rules_to_delete:
                        print(f"🗑️  Deleting {len(rules_to_delete)} listener rule(s) that reference this target group...")
                        for rule in rules_to_delete:
                            try:
                                elbv2.delete_rule(RuleArn=rule["RuleArn"])
                                print(f"   ✅ Deleted rule with priority {rule.get('Priority')}")
                            except ClientError as e:
                                print(f"   ⚠️  Failed to delete rule {rule.get('Priority')}: {e}")
                
                # Now delete the target group
                print("🗑️  Deleting target group...")
                elbv2.delete_target_group(TargetGroupArn=existing['TargetGroupArn'])
                print(f"✅ Deleted existing target group")
                
                # Wait a moment for deletion to complete
                import time
                time.sleep(3)
                
                # Set existing to None so it will be recreated below
                existing = None
            except ClientError as e:
                print(f"❌ Failed to delete target group: {e}", file=sys.stderr)
                print(f"   Error code: {e.response.get('Error', {}).get('Code')}")
                sys.exit(1)
        else:
            print(f"\n✅ Reusing existing Target Group: {new_tg_name} ({existing['TargetGroupArn']})")
            print(f"   Configuration: {existing_protocol}:{existing_port}")
            new_tg_arn = existing["TargetGroupArn"]
    
    if not existing:
        print("\nCreating Target Group...")
        create_args = {
            "Name": new_tg_name,
            "Protocol": target_protocol,
            "Port": target_port,
            "VpcId": vpc_id,
            "HealthCheckPath": health_path,
            "Matcher": {"HttpCode": matcher},
            "TargetType": target_type,
        }
        if target_protocol == "HTTPS":
            create_args["HealthCheckProtocol"] = "HTTPS"

        resp = elbv2.create_target_group(**create_args)
        new_tg_arn = resp["TargetGroups"][0]["TargetGroupArn"]
        print(f"Created Target Group: {new_tg_name} ({new_tg_arn})")

    # Register targets (instances or IPs) from YAML or prompt
    register_targets(elbv2, new_tg_arn, target_type, target_port, cfg)

    # Quick health check snapshot (no waiting loop; just immediate state)
    print_target_health(elbv2, new_tg_arn)

    # Prepare rule conditions
    conditions = []
    if new_host:
        conditions.append({
            "Field": "host-header",
            "HostHeaderConfig": {"Values": [new_host]}
        })
    conditions.append({
        "Field": "path-pattern",
        "PathPatternConfig": {"Values": [new_path]}
    })

    # Check if a rule with this path pattern already exists
    print(f"\n🔍 Checking for existing rules with path pattern '{new_path}'...")
    rules = list_rules_for_listener(elbv2, listener["ListenerArn"])
    
    rule_exists = False
    for rule in rules:
        if rule.get("Priority") == "default":
            continue
        
        existing_paths = extract_path_patterns(rule)
        existing_hosts = extract_host_values(rule)
        
        # Check if path matches
        if new_path in existing_paths:
            # If host is specified, check if it matches too
            if new_host:
                if not existing_hosts or new_host in existing_hosts:
                    rule_exists = True
                    print(f"✅ Rule already exists with priority {rule.get('Priority')}")
                    print(f"   Host: {new_host if new_host else '<any>'}")
                    print(f"   Path: {new_path}")
                    print(f"   Skipping rule creation.")
                    break
            else:
                # No host specified, just path match is enough
                rule_exists = True
                print(f"✅ Rule already exists with priority {rule.get('Priority')}")
                print(f"   Path: {new_path}")
                print(f"   Skipping rule creation.")
                break
    
    if not rule_exists:
        # Choose a free priority and create rule
        prio = next_free_priority(rules)

        print(f"\nCreating listener rule on port {listener_port} with priority {prio}...")
        try:
            elbv2.create_rule(
                ListenerArn=listener["ListenerArn"],
                Priority=prio,
                Conditions=conditions,
                Actions=[{
                    "Type": "forward",
                    "TargetGroupArn": new_tg_arn
                }]
            )
            print("✅ Rule created successfully.")
        except ClientError as e:
            print(f"Failed to create rule: {e}", file=sys.stderr)
            sys.exit(1)

    print("\nDone. Summary:")
    print(f"- Listener: {listener_port}")
    if new_host:
        print(f"- Host: {new_host}")
    print(f"- Path: {new_path}")
    print(f"- Target Group: {new_tg_name} (port {target_port}, protocol {target_protocol}, type {target_type})")
    print("\nNext steps:")
    print("- Confirm health checks become healthy (may take ~30–60s).")
    host_for_test = new_host if new_host else "<your-host>"
    path_for_test = new_path.rstrip("*") + "/"
    print(f"- Test via ALB: curl -vkI https://{host_for_test}{path_for_test}")

if __name__ == "__main__":
    main()
