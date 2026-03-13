"""
NE301 project initialization tool
Automatically download and initialize NE301 project on application startup
"""
import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional
from backend.config import settings

NE301_REPO_URL = "https://github.com/camthink-ai/ne301.git"
DEFAULT_NE301_PATH = Path("/app/ne301")


def ensure_ne301_project(ne301_path: Optional[Path] = None) -> Path:
    """
    Ensure NE301 project exists, auto-clone if not exists
    
    Args:
        ne301_path: NE301 project path, if None use default path or path from config
    
    Returns:
        NE301 project path
    """
    # Determine target path
    if ne301_path is None:
        # Prefer using path from environment variable or config
        env_path = os.environ.get("NE301_PROJECT_PATH")
        if env_path:
            ne301_path = Path(env_path)
        elif hasattr(settings, 'NE301_PROJECT_PATH') and settings.NE301_PROJECT_PATH:
            ne301_path = Path(settings.NE301_PROJECT_PATH)
        else:
            # Use default path
            ne301_path = DEFAULT_NE301_PATH
    
    ne301_path = Path(ne301_path).resolve()
    
    # Check mounted host directory (/workspace/ne301)
    # In Docker Compose, host directory is mounted to /workspace/ne301
    workspace_path = Path("/workspace/ne301")
    if workspace_path.exists() and workspace_path.is_dir():
        # Check if empty directory or symlink
        try:
            if not any(workspace_path.iterdir()):
                # Empty directory, clone project
                print(f"[NE301] Workspace directory is empty, cloning to {workspace_path}")
                subprocess.run(
                    ["git", "clone", NE301_REPO_URL, str(workspace_path)],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"[NE301] Successfully cloned to workspace: {workspace_path}")
            # Use workspace directory
            ne301_path = workspace_path
        except Exception as e:
            print(f"[NE301] Warning: Failed to use workspace directory: {e}")
    
    # If directory doesn't exist, clone
    if not ne301_path.exists():
        print(f"[NE301] Project directory not found: {ne301_path}")
        print(f"[NE301] Cloning NE301 project from {NE301_REPO_URL}...")
        
        try:
            # Check if git is available
            subprocess.run(
                ["git", "--version"],
                check=True,
                capture_output=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[NE301] ERROR: git is not available. Cannot clone NE301 project.")
            print("[NE301] Please install git in Dockerfile or mount the project manually.")
            return ne301_path
        
        # Create parent directory
        ne301_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Clone project
        try:
            subprocess.run(
                ["git", "clone", NE301_REPO_URL, str(ne301_path)],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"[NE301] Successfully cloned NE301 project to {ne301_path}")
        except subprocess.CalledProcessError as e:
            print(f"[NE301] ERROR: Failed to clone NE301 project: {e}")
            print(f"[NE301] stdout: {e.stdout}")
            print(f"[NE301] stderr: {e.stderr}")
            print(f"[NE301] You can manually clone the project or set NE301_PROJECT_PATH to an existing path.")
            return ne301_path
    
    # If directory exists but is empty, try to clone
    if ne301_path.exists() and ne301_path.is_dir():
        try:
            if not any(ne301_path.iterdir()):
                print(f"[NE301] Directory exists but is empty, cloning...")
                subprocess.run(
                    ["git", "clone", NE301_REPO_URL, str(ne301_path)],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"[NE301] Successfully cloned to {ne301_path}")
        except Exception as e:
            print(f"[NE301] Warning: Directory check failed: {e}")
    
    # Verify project structure
    model_dir = ne301_path / "Model"
    makefile = ne301_path / "Makefile"
    
    if not model_dir.exists():
        print(f"[NE301] WARNING: Model directory not found in {ne301_path}")
        return ne301_path
    
    if not makefile.exists():
        print(f"[NE301] WARNING: Makefile not found in {ne301_path}")
        return ne301_path
    
    print(f"[NE301] Project ready at: {ne301_path}")
    return ne301_path


def get_ne301_project_path() -> Path:
    """
    Get NE301 project path (auto-initialize if not exists)
    
    Returns:
        NE301 project path
    """
    return ensure_ne301_project()


if __name__ == "__main__":
    # Test
    path = ensure_ne301_project()
    print(f"NE301 project path: {path}")
