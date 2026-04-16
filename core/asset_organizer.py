"""
Asset Organizer
Creates project folders and organizes all generated assets
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List


class AssetOrganizer:
    """Organizes images and audio into project folders"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path).resolve()
        self.projects_folder = self.base_path / "projects"
        
    def create_project(self, project_name: str) -> Dict[str, Path]:
        """Create project folder structure"""
        # Sanitize project name
        safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in project_name)
        safe_name = safe_name.strip().replace(" ", "_")
        
        # Create project folder
        project_folder = self.projects_folder / safe_name
        images_folder = project_folder / "images"
        audio_folder = project_folder / "audio"
        
        # Create directories
        project_folder.mkdir(parents=True, exist_ok=True)
        images_folder.mkdir(exist_ok=True)
        audio_folder.mkdir(exist_ok=True)
        
        print(f"Created project folder: {project_folder}")
        print(f"  Images: {images_folder}")
        print(f"  Audio: {audio_folder}")
        
        return {
            "project": project_folder,
            "images": images_folder,
            "audio": audio_folder
        }
    
    def list_assets(self, project_name: str) -> Dict[str, List[Path]]:
        """List all assets in a project"""
        safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in project_name)
        safe_name = safe_name.strip().replace(" ", "_")
        
        project_folder = self.projects_folder / safe_name
        images_folder = project_folder / "images"
        audio_folder = project_folder / "audio"
        
        images = sorted(images_folder.glob("*.jpg")) + sorted(images_folder.glob("*.png"))
        audio = sorted(audio_folder.glob("*.mp3")) + sorted(audio_folder.glob("*.wav"))
        
        return {
            "images": images,
            "audio": audio,
            "total": len(images) + len(audio)
        }
    
    def get_summary(self, project_name: str) -> str:
        """Get formatted summary of project assets"""
        assets = self.list_assets(project_name)
        
        summary = f"""
{'='*60}
PROJECT: {project_name}
{'='*60}
IMAGES ({len(assets['images'])}):
"""
        for img in assets['images']:
            summary += f"  - {img.name}\n"
        
        summary += f"""
AUDIO ({len(assets['audio'])}):
"""
        for aud in assets['audio']:
            summary += f"  - {aud.name}\n"
        
        summary += f"{'='*60}\n"
        
        return summary
    
    def clean_project(self, project_name: str, confirm: bool = True):
        """Clean project folder (use with caution)"""
        if confirm:
            response = input(f"Are you sure you want to delete '{project_name}'? (yes/no): ")
            if response.lower() != "yes":
                print("Cancelled.")
                return
        
        safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in project_name)
        safe_name = safe_name.strip().replace(" ", "_")
        project_folder = self.projects_folder / safe_name
        
        if project_folder.exists():
            shutil.rmtree(project_folder)
            print(f"Deleted: {project_folder}")
        else:
            print(f"Project not found: {project_name}")
