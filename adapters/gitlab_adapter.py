"""
GitLab Bug Bounty Adapter for ZQM Bounty Hub

This adapter provides integration with GitLab's bug bounty and security research programs.
It handles authentication, target enumeration, and evidence collection.
"""

import os
import json
import requests
from typing import Dict, List, Optional
from datetime import datetime


class GitLabAdapter:
    """GitLab bug bounty platform adapter."""
    
    PLATFORM_ID = "gitlab"
    BASE_URL = "https://gitlab.com/api/v4"
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize GitLab adapter.
        
        Args:
            api_token: GitLab personal access token (or from env var GITLAB_API_TOKEN)
        """
        self.api_token = api_token or os.getenv("GITLAB_API_TOKEN")
        if not self.api_token:
            raise ValueError("GITLAB_API_TOKEN environment variable not set")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Private-Token": self.api_token,
            "Content-Type": "application/json"
        })
    
    def verify_auth(self) -> Dict:
        """
        Verify authentication with GitLab API.
        
        Returns:
            Dict with auth status and user info
        """
        try:
            resp = self.session.get(f"{self.BASE_URL}/user")
            resp.raise_for_status()
            user = resp.json()
            
            return {
                "status": "verified",
                "user": user.get("username"),
                "email": user.get("public_email"),
                "verified_at": datetime.utcnow().isoformat() + "Z"
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "verified_at": datetime.utcnow().isoformat() + "Z"
            }
    
    def get_program_targets(self, program_id: str) -> Dict:
        """
        Get targets for a specific GitLab bug bounty program.
        
        Args:
            program_id: GitLab project ID or namespace/project path
            
        Returns:
            Dict with target information
        """
        try:
            # Get project info
            resp = self.session.get(f"{self.BASE_URL}/projects/{program_id}")
            resp.raise_for_status()
            project = resp.json()
            
            # Get issues (potential bounty targets)
            resp = self.session.get(
                f"{self.BASE_URL}/projects/{program_id}/issues",
                params={"state": "opened", "per_page": 100}
            )
            resp.raise_for_status()
            issues = resp.json()
            
            return {
                "platform": "gitlab",
                "target_id": program_id,
                "project_name": project.get("name"),
                "project_path": project.get("path_with_namespace"),
                "issues_count": len(issues),
                "issues": [
                    {
                        "id": issue.get("iid"),
                        "title": issue.get("title"),
                        "labels": issue.get("labels", []),
                        "created_at": issue.get("created_at")
                    }
                    for issue in issues[:10]  # Limit to 10
                ]
            }
        except Exception as e:
            return {
                "platform": "gitlab",
                "target_id": program_id,
                "status": "error",
                "error": str(e)
            }
    
    def search_vulnerabilities(self, query: str) -> List[Dict]:
        """
        Search for vulnerability-related issues across GitLab.
        
        Args:
            query: Search query (e.g., "security", "vulnerability", "CVE-")
            
        Returns:
            List of matching issues
        """
        try:
            resp = self.session.get(
                f"{self.BASE_URL}/issues",
                params={"search": query, "scope": "all", "per_page": 50}
            )
            resp.raise_for_status()
            issues = resp.json()
            
            return [
                {
                    "platform": "gitlab",
                    "id": issue.get("id"),
                    "title": issue.get("title"),
                    "project": issue.get("namespace", {}).get("full_path"),
                    "url": issue.get("web_url"),
                    "created_at": issue.get("created_at")
                }
                for issue in issues
            ]
        except Exception as e:
            return []
    
    def get_merge_requests(self, project_id: str, state: str = "all") -> Dict:
        """
        Get merge requests for a project (potential security fixes).
        
        Args:
            project_id: GitLab project ID
            state: Filter by state (all, opened, closed, merged)
            
        Returns:
            Dict with merge request information
        """
        try:
            resp = self.session.get(
                f"{self.BASE_URL}/projects/{project_id}/merge_requests",
                params={"state": state, "per_page": 100}
            )
            resp.raise_for_status()
            mrs = resp.json()
            
            return {
                "platform": "gitlab",
                "target_id": project_id,
                "merge_requests_count": len(mrs),
                "merge_requests": [
                    {
                        "id": mr.get("iid"),
                        "title": mr.get("title"),
                        "state": mr.get("state"),
                        "merged": mr.get("merged"),
                        "created_at": mr.get("created_at")
                    }
                    for mr in mrs[:10]
                ]
            }
        except Exception as e:
            return {
                "platform": "gitlab",
                "target_id": project_id,
                "status": "error",
                "error": str(e)
            }
    
    def run_security_checks(self, target_id: str, check_types: List[str]) -> Dict:
        """
        Run security checks on a GitLab target.
        
        Args:
            target_id: GitLab project ID
            check_types: List of check types (e.g., ["web_app", "api"])
            
        Returns:
            Dict with check results
        """
        results = {
            "platform": "gitlab",
            "target_id": target_id,
            "checks_run": [],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if "web_app" in check_types or "api" in check_types:
            # Check for exposed secrets in issues/MRs
            issues = self.search_vulnerabilities("password OR secret OR token")
            results["checks_run"].append({
                "check_type": "secret_exposure",
                "status": "completed",
                "findings_count": len(issues),
                "findings": issues[:5]
            })
        
        if "web_app" in check_types:
            # Get project info for web app checks
            project_info = self.get_program_targets(target_id)
            results["checks_run"].append({
                "check_type": "web_app_recon",
                "status": "completed",
                "project_info": project_info
            })
        
        return results


# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: gitlab_adapter.py <command> [args...]")
        print("Commands:")
        print("  verify-auth                    - Verify authentication")
        print("  get-targets <project_id>       - Get program targets")
        print("  search <query>                 - Search vulnerabilities")
        print("  get-mrs <project_id>           - Get merge requests")
        print("  run-checks <project_id> <types> - Run security checks")
        sys.exit(1)
    
    command = sys.argv[1]
    adapter = GitLabAdapter()
    
    if command == "verify-auth":
        result = adapter.verify_auth()
        print(json.dumps(result, indent=2))
    
    elif command == "get-targets" and len(sys.argv) > 2:
        result = adapter.get_program_targets(sys.argv[2])
        print(json.dumps(result, indent=2))
    
    elif command == "search" and len(sys.argv) > 2:
        results = adapter.search_vulnerabilities(sys.argv[2])
        print(json.dumps(results, indent=2))
    
    elif command == "get-mrs" and len(sys.argv) > 2:
        result = adapter.get_merge_requests(sys.argv[2])
        print(json.dumps(result, indent=2))
    
    elif command == "run-checks" and len(sys.argv) > 3:
        check_types = sys.argv[3].split(",")
        result = adapter.run_security_checks(sys.argv[2], check_types)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)