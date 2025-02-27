# code_manager.py

import os
import shutil
import logging
from git import Repo  # Requires: pip install GitPython

logger = logging.getLogger(__name__)

def get_code(source, destination):
    """
    Copies or clones the code from a source to the destination directory.
    
    Parameters:
      source: A git repository URL (if it starts with http://, https://, or ends with .git) or a local directory path.
      destination: The local directory where the code should be placed.
    """
    if source.startswith("http://") or source.startswith("https://") or source.endswith(".git"):
        logger.info(f"Cloning git repository {source} to {destination}")
        try:
            Repo.clone_from(source, destination)
            logger.info("Repository cloned successfully.")
        except Exception as e:
            logger.error(f"Error cloning repository: {str(e)}")
            raise
    else:
        logger.info(f"Copying code from local path {source} to {destination}")
        try:
            if os.path.exists(destination):
                shutil.rmtree(destination)
            shutil.copytree(source, destination)
            logger.info("Code copied successfully.")
        except Exception as e:
            logger.error(f"Error copying code: {str(e)}")
            raise
