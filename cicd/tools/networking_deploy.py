#!/usr/bin/env python3
"""
Add a single ingress rule allowing traffic from one Security Group to another,
for a single target_port, using a minimal YAML config.

YAML fields (minimal):
  region: us-west-1               # optional, default us-west-1
  target_sg_id: sg-aaaaaaaaaaaaaaa  # REQUIRED (receives the rule)
  source_sg_id: sg-bbbbbbbbbbbbbbb  # REQUIRED (allowed to connect)
  target_port: 8443                        # REQUIRED
  protocol: tcp                     # optional, default tcp
  description: "App -> Backend"     # optional

Usage:
  python add_ingress_from_yaml.py config.yaml

Prereqs:
  pip install boto3 pyyaml
"""

import sys
import boto3
from botocore.exceptions import ClientError
import yaml


def load_cfg(path: str) -> dict:
    try:
        with open(path, "r") as f:
            cfg = yaml.safe_load(f) or {}
    except FileNotFoundError:
        sys.exit(f"Config file not found: {path}")
    except Exception as e:
        sys.exit(f"Failed to read YAML: {e}")

    # Minimal validation
    required = ["target_sg_id", "source_sg_id", "target_port"]
    missing = [k for k in required if cfg.get(k) in (None, "")]
    if missing:
        sys.exit(f"Missing required YAML fields: {', '.join(missing)}")

    # Defaults
    cfg.setdefault("region", "us-west-1")
    cfg.setdefault("protocol", "tcp")
    return cfg


def rule_already_exists(ec2, target_sg_id: str, proto: str, target_port: int, source_sg_id: str) -> bool:
    resp = ec2.describe_security_groups(GroupIds=[target_sg_id])
    sgs = resp.get("SecurityGroups", [])
    if not sgs:
        sys.exit(f"Target Security Group not found: {target_sg_id}")

    for perm in sgs[0].get("IpPermissions", []):
        if perm.get("IpProtocol") not in (proto, "-1"):
            continue

        # For tcp/udp ensure target_port matches; for '-1' (all), treat as already covered
        if proto in ("tcp", "udp"):
            if perm.get("FromPort") is None or perm.get("ToPort") is None:
                # e.g. protocol -1 (all) already present
                pass
            elif not (perm["FromPort"] <= target_port <= perm["ToPort"]):
                continue

        for pair in perm.get("UserIdGroupPairs", []):
            if pair.get("GroupId") == source_sg_id:
                return True
    return False


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python add_ingress_from_yaml.py <config.yaml>")

    cfg = load_cfg(sys.argv[1])
    region = cfg["region"]
    target_sg_id = cfg["target_sg_id"]
    source_sg_id = cfg["source_sg_id"]
    target_port = int(cfg["target_port"])
    proto = cfg["protocol"].lower()
    if proto == "all":
        boto_proto = "-1"
    else:
        boto_proto = proto
    description = cfg.get("description")

    ec2 = boto3.client("ec2", region_name=region)

    if rule_already_exists(ec2, target_sg_id, boto_proto, target_port, source_sg_id):
        print("Rule already exists — nothing to do. ✅")
        return

    perm = {
        "IpProtocol": boto_proto,
        "UserIdGroupPairs": [{"GroupId": source_sg_id}],
    }
    if boto_proto in ("tcp", "udp"):
        perm["FromPort"] = target_port
        perm["ToPort"] = target_port
    if description:
        # AWS allows description on each pair
        perm["UserIdGroupPairs"][0]["Description"] = description

    try:
        ec2.authorize_security_group_ingress(
            GroupId=target_sg_id,
            IpPermissions=[perm],
        )
        print(
            f"Added ingress: {proto.upper()} {target_port} from {source_sg_id} -> {target_sg_id} in {region}. ✅"
        )
    except ClientError as e:
        # If duplicate due to eventual consistency, show friendly message
        code = e.response.get("Error", {}).get("Code")
        if code in ("InvalidPermission.Duplicate",):
            print("Rule already exists (AWS reported duplicate). ✅")
        else:
            raise


if __name__ == "__main__":
    main()
