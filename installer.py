import subprocess
import sys
import logging
import os

class AutoInstaller:
    def __init__(self, requirements_path="requirements.txt"):
        # Resolve path relative to this file if default is used
        if requirements_path == "requirements.txt":
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.req_path = os.path.join(base_dir, requirements_path)
        else:
            self.req_path = requirements_path
            
        self.logger = logging.getLogger("NexusV2.Installer")

    def check_dependencies(self):
        """Check if dependencies in requirements.txt are installed."""
        if not os.path.exists(self.req_path):
            self.logger.error(f"Requirements file not found: {self.req_path}")
            return False, []

        self.logger.info("Checking dependencies...")
        try:
            # Get installed packages
            installed = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode('utf-8')
            installed_packages = {line.split('==')[0].lower() for line in installed.splitlines() if '==' in line}
            
            with open(self.req_path, 'r') as f:
                required = [line.strip().split('>=')[0].split('==')[0].lower() for line in f if line.strip() and not line.startswith('#')]
            
            missing = [pkg for pkg in required if pkg not in installed_packages]
            
            if missing:
                self.logger.warning(f"Missing dependencies: {missing}")
                return False, missing
            
            self.logger.info("All dependencies are satisfied.")
            return True, []
        except Exception as e:
            self.logger.error(f"Error checking dependencies: {e}")
            return False, []

    def install_dependencies(self):
        """Install missing dependencies."""
        success, missing = self.check_dependencies()
        if success:
            return True

        if not missing:
            # Check failed but no specific missing list returned (error case)
            return False

        self.logger.info(f"Installing missing packages: {missing}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
            self.logger.info("Installation successful.")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Installation failed: {e}")
            return False
