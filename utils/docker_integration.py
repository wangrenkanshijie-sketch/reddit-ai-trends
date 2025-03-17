"""
Docker Integration

This module provides functionality to containerize the application.
"""

import os
import logging
from typing import Dict, Any, Optional
from config import DOCKER_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DockerIntegration:
    """Service for integrating with Docker."""
    
    def __init__(self, project_path: Optional[str] = None):
        """
        Initialize the Docker integration.
        
        Args:
            project_path: Optional path to the project directory
        """
        self.project_path = project_path or os.path.abspath('.')
        self.image_name = DOCKER_CONFIG['image_name']
        self.container_name = DOCKER_CONFIG['container_name']
        self.port = DOCKER_CONFIG['port']
        
        logger.info(f"Docker integration initialized for project at {self.project_path}")
    
    def generate_dockerfile(self) -> str:
        """
        Generate a Dockerfile for the application.
        
        Returns:
            Path to the generated Dockerfile
        """
        dockerfile_path = os.path.join(self.project_path, 'Dockerfile')
        
        with open(dockerfile_path, 'w', encoding='utf-8') as f:
            f.write("""FROM python:3.9-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create reports directory
RUN mkdir -p reports

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "report_generation.py"]
""")
        
        logger.info(f"Dockerfile generated at {dockerfile_path}")
        return dockerfile_path
    
    def generate_docker_compose(self) -> str:
        """
        Generate a docker-compose.yml file for the application.
        
        Returns:
            Path to the generated docker-compose.yml file
        """
        docker_compose_path = os.path.join(self.project_path, 'docker-compose.yml')
        
        with open(docker_compose_path, 'w', encoding='utf-8') as f:
            f.write(f"""version: '3'

services:
  app:
    build: .
    container_name: {self.container_name}
    volumes:
      - ./reports:/app/reports
      - ./.env:/app/.env
    environment:
      - TZ=UTC
    restart: unless-stopped
""")
        
        logger.info(f"docker-compose.yml generated at {docker_compose_path}")
        return docker_compose_path
    
    def generate_dockerignore(self) -> str:
        """
        Generate a .dockerignore file for the application.
        
        Returns:
            Path to the generated .dockerignore file
        """
        dockerignore_path = os.path.join(self.project_path, '.dockerignore')
        
        with open(dockerignore_path, 'w', encoding='utf-8') as f:
            f.write("""# Git
.git
.gitignore

# Docker
Dockerfile
docker-compose.yml
.dockerignore

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Reports
reports/

# Environment variables
.env
.env_sample
""")
        
        logger.info(f".dockerignore generated at {dockerignore_path}")
        return dockerignore_path
    
    def setup_docker_environment(self) -> Dict[str, str]:
        """
        Set up the Docker environment by generating all necessary files.
        
        Returns:
            Dictionary with paths to generated files
        """
        logger.info("Setting up Docker environment")
        
        dockerfile_path = self.generate_dockerfile()
        docker_compose_path = self.generate_docker_compose()
        dockerignore_path = self.generate_dockerignore()
        
        return {
            "dockerfile": dockerfile_path,
            "docker_compose": docker_compose_path,
            "dockerignore": dockerignore_path
        } 