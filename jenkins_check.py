"""
DeploySentry AI — Jenkins Integration Script

This is the script Jenkins actually runs as a pipeline step, BEFORE deploying.
It calls the DeploySentry /evaluate API, prints the decision so it shows up
in the Jenkins console log, and exits with a code Jenkins understands:

    exit code 0  -> APPROVE  -> pipeline continues normally
    exit code 1  -> BLOCK    -> pipeline fails/stops immediately
    exit code 2  -> REVIEW   -> pipeline pauses for manual approval

Usage (this is exactly what a Jenkinsfile would call):
    python jenkins_check.py --files "auth/login.py,frontend/style.css" \
                             --lines 40 --branch feature/fix-login --pr true
"""

import argparse
import sys

import requests

API_URL = "http://localhost:8090/evaluate"  # change to your deployed URL later

EXIT_CODES = {
    "APPROVE": 0,
    "REVIEW": 2,
    "BLOCK": 1,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", required=True, help="Comma-separated list of changed files")
    parser.add_argument("--lines", required=True, type=int, help="Number of lines changed")
    parser.add_argument("--branch", required=True, help="Branch name")
    parser.add_argument("--pr", required=True, help="true/false - was this a pull request")
    args = parser.parse_args()

    payload = {
        "files_changed": [f.strip() for f in args.files.split(",")],
        "lines_changed": args.lines,
        "branch": args.branch,
        "is_pull_request": args.pr.lower() == "true",
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Could not reach DeploySentry API: {e}")
        sys.exit(1)  # fail safe: if we can't check, block the deploy

    result = response.json()
    action = result["action"]
    reason = result.get("reason", "")
    rule = result.get("matched_rule", "")

    print("=" * 50)
    print(f"DeploySentry Decision: {action}")
    print(f"Matched Rule: {rule}")
    print(f"Reason: {reason}")
    print("=" * 50)

    sys.exit(EXIT_CODES.get(action, 1))


if __name__ == "__main__":
    main()
