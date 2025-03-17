"""
GitHub Integration

This module provides functionality to push reports to a GitHub repository.
"""

import os
import logging
import git
from datetime import datetime
from typing import Dict, Any, Optional
from config import GITHUB_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubIntegration:
    """Service for integrating with GitHub."""
    
    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize the GitHub integration.
        
        Args:
            repo_path: Optional path to the local repository
        """
        self.repo_path = repo_path or os.path.abspath('.')
        self.repo_name = GITHUB_CONFIG['repo_name']
        self.branch = GITHUB_CONFIG['branch']
        
        # Check if the repository exists
        if not os.path.exists(os.path.join(self.repo_path, '.git')):
            logger.warning(f"Git repository not found at {self.repo_path}")
        else:
            logger.info(f"Git repository found at {self.repo_path}")
    
    def commit_and_push_report(self, report_path: str, report_metadata: Dict[str, Any]) -> bool:
        """
        Commit and push a report to GitHub.
        
        Args:
            report_path: Path to the report file
            report_metadata: Report metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the repository
            repo = git.Repo(self.repo_path)
            
            # Check if the file is within the repository
            relative_path = os.path.relpath(report_path, self.repo_path)
            if relative_path.startswith('..'):
                logger.error(f"Report file {report_path} is not within the repository {self.repo_path}")
                return False
            
            # Add the file to the index
            repo.git.add(report_path)
            
            # Also add the metadata file if it exists
            metadata_path = report_path.replace('.md', '_metadata.json')
            if os.path.exists(metadata_path):
                repo.git.add(metadata_path)
            
            # Create the commit message
            timestamp = report_metadata.get('timestamp', datetime.utcnow())
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except ValueError:
                    timestamp = datetime.utcnow()
            
            commit_message = GITHUB_CONFIG['commit_message_format'].format(
                date=timestamp.strftime('%Y-%m-%d %H:%M UTC')
            )
            
            # Commit the changes
            repo.git.commit('-m', commit_message)
            
            # Push to GitHub
            repo.git.push('origin', self.branch)
            
            logger.info(f"Successfully pushed report to GitHub: {relative_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error pushing report to GitHub: {e}")
            return False
    
    def initialize_repository(self) -> bool:
        """
        Initialize a new Git repository if it doesn't exist.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if the repository already exists
            if os.path.exists(os.path.join(self.repo_path, '.git')):
                logger.info(f"Git repository already exists at {self.repo_path}")
                return True
            
            # Create the repository
            repo = git.Repo.init(self.repo_path)
            
            # Create a README.md file
            readme_path = os.path.join(self.repo_path, 'README.md')
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(f"""# {self.repo_name}

This repository contains automatically generated reports of trending posts from AI and technology communities on Reddit.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
""")
            
            # Create a LICENSE file
            license_path = os.path.join(self.repo_path, 'LICENSE')
            with open(license_path, 'w', encoding='utf-8') as f:
                f.write("""MIT License

Copyright (c) 2023 Reddit AI Report

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""")
            
            # Add the files to the index
            repo.git.add(readme_path)
            repo.git.add(license_path)
            
            # Commit the changes
            repo.git.commit('-m', 'Initial commit')
            
            logger.info(f"Successfully initialized Git repository at {self.repo_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error initializing Git repository: {e}")
            return False 