import requests
import json
import os
import time
import threading
from typing import Optional, List, Dict, Any
from utils.logger import get_logger
from config import Config

logger = get_logger("github")

class GitHubClient:
    """
    GitHub API client for repository analysis, code reading, and PR creation.
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self):
        self.token = Config.get("github.token", "")
        self.username = Config.get("github.username", "")
        self._headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if self.token:
            self._headers["Authorization"] = f"token {self.token}"
    
    def _request(self, method: str, url: str, **kwargs) -> Optional[Dict]:
        try:
            full_url = f"{self.BASE_URL}{url}"
            response = requests.request(method, full_url, headers=self._headers, timeout=30, **kwargs)
            
            if response.status_code == 403 and "rate limit" in response.text.lower():
                reset = response.headers.get("X-RateLimit-Reset")
                if reset:
                    wait_time = int(reset) - int(time.time())
                    logger.warning(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(max(wait_time, 0))
                    return self._request(method, url, **kwargs)
            
            response.raise_for_status()
            
            if response.status_code == 204:
                return {}
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API error: {e}")
            return None
    
    def get_user(self) -> Optional[Dict]:
        return self._request("GET", "/user")
    
    def get_repo(self, owner: str, repo: str) -> Optional[Dict]:
        return self._request("GET", f"/repos/{owner}/{repo}")
    
    def list_user_repos(self, username: str = None, per_page: int = 100) -> List[Dict]:
        username = username or self.username
        repos = []
        page = 1
        while True:
            result = self._request("GET", f"/users/{username}/repos", params={
                "per_page": per_page,
                "page": page,
                "type": "all"
            })
            if not result or not isinstance(result, list):
                break
            repos.extend(result)
            if len(result) < per_page:
                break
            page += 1
        return repos
    
    def search_repos(self, query: str, per_page: int = 10) -> List[Dict]:
        return self._request("GET", "/search/repositories", params={
            "q": query,
            "per_page": per_page,
            "sort": "stars",
            "order": "desc"
        }) or {}
    
    def get_repo_contents(self, owner: str, repo: str, path: str = "") -> List[Dict]:
        url = f"/repos/{owner}/{repo}/contents/{path}"
        result = self._request("GET", url)
        if result and isinstance(result, list):
            return result
        return []
    
    def get_file_content(self, owner: str, repo: str, path: str, ref: str = "main") -> Optional[str]:
        result = self._request("GET", f"/repos/{owner}/{repo}/contents/{path}", params={"ref": ref})
        if result and "content" in result:
            import base64
            try:
                content = base64.b64decode(result["content"])
                return content.decode("utf-8", errors="replace")
            except Exception as e:
                logger.error(f"Error decoding file content: {e}")
        return None
    
    def get_repo_tree(self, owner: str, repo: str, ref: str = "main") -> List[Dict]:
        result = self._request("GET", f"/repos/{owner}/{repo}/git/trees/{ref}", params={
            "recursive": "1"
        })
        if result and "tree" in result:
            return result["tree"]
        return []
    
    def get_repo_issues(self, owner: str, repo: str, state: str = "open", per_page: int = 30) -> List[Dict]:
        result = self._request("GET", f"/repos/{owner}/{repo}/issues", params={
            "state": state,
            "per_page": per_page
        })
        if result and isinstance(result, list):
            return result
        return []
    
    def create_issue(self, owner: str, repo: str, title: str, body: str = "", labels: List[str] = None) -> Optional[Dict]:
        payload = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
        return self._request("POST", f"/repos/{owner}/{repo}/issues", json=payload)
    
    def create_pull_request(self, owner: str, repo: str, title: str, body: str, head: str, base: str = "main") -> Optional[Dict]:
        payload = {
            "title": title,
            "head": head,
            "base": base,
            "body": body
        }
        return self._request("POST", f"/repos/{owner}/{repo}/pulls", json=payload)
    
    def commit_file(self, owner: str, repo: str, path: str, content: str, message: str, branch: str = "main"):
        """Create or update a file in the repository."""
        try:
            existing = self._request("GET", f"/repos/{owner}/{repo}/contents/{path}", params={"ref": branch})
            
            import base64
            encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
            
            if existing and "sha" in existing:
                sha = existing["sha"]
                payload = {
                    "message": message,
                    "content": encoded_content,
                    "sha": sha,
                    "branch": branch
                }
            else:
                payload = {
                    "message": message,
                    "content": encoded_content,
                    "branch": branch
                }
            
            return self._request("PUT", f"/repos/{owner}/{repo}/contents/{path}", json=payload)
            
        except Exception as e:
            logger.error(f"Error committing file: {e}")
            return None
    
    def list_branches(self, owner: str, repo: str) -> List[Dict]:
        result = self._request("GET", f"/repos/{owner}/{repo}/branches", params={"per_page": 100})
        if result and isinstance(result, list):
            return result
        return []
    
    def search_code(self, query: str, per_page: int = 10) -> List[Dict]:
        result = self._request("GET", "/search/code", params={
            "q": query,
            "per_page": per_page
        })
        if result and "items" in result:
            return result["items"]
        return []
    
    def get_repo_readme(self, owner: str, repo: str) -> Optional[str]:
        result = self._request("GET", f"/repos/{owner}/{repo}/readme")
        if result and "content" in result:
            import base64
            try:
                content = base64.b64decode(result["content"])
                return content.decode("utf-8", errors="replace")
            except Exception:
                pass
        return None
    
    def get_repo_languages(self, owner: str, repo: str) -> Dict[str, int]:
        result = self._request("GET", f"/repos/{owner}/{repo}/languages")
        if result and isinstance(result, dict):
            return result
        return {}
    
    def get_repo_contributors(self, owner: str, repo: str) -> List[Dict]:
        result = self._request("GET", f"/repos/{owner}/{repo}/contributors")
        if result and isinstance(result, list):
            return result
        return []
