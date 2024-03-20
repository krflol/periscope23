import subprocess
import shutil
import os

# Specify your FastAPI application file (or files) here
app_files = ["main.py", ".env"]  # Add other files as needed
requirements_file = "requirements.txt"  # Path to your requirements file

# Setup virtual environment directory name
venv_dir = "venv_lambda"

# Path to the Python 3.11 executable
# Adjust this according to the actual location or command for Python 3.11 on your system
python_executable = "python"  # or use the full path if `python3.11` is not directly accessible

# Create virtual environment with Python 3.11 using subprocess
subprocess.run([python_executable, "-m", "venv", venv_dir], check=True)

# Windows-specific paths for the virtual environment
pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
python_path = os.path.join(venv_dir, "Scripts", "python.exe")

# Activate the virtual environment and install dependencies
pip_install_cmd = [pip_path, "install", "-r", requirements_file]
subprocess.run(pip_install_cmd, check=True)

# Install additional dependencies required by AWS Lambda & FastAPI
additional_packages = ["fastapi", "uvicorn", "mangum"]
subprocess.run([pip_path, "install"] + additional_packages, check=True)

# Use subprocess to get the site-packages directory path
site_packages_dir = subprocess.check_output([python_path, "-c", "import site; print(site.getsitepackages()[0])"], text=True).strip()

# Create a /temp_images directory inside the package
temp_images_dir = os.path.join(site_packages_dir, "temp_images")
os.makedirs(temp_images_dir, exist_ok=True)

# Copy app files to the site-packages directory
for file in app_files:
    shutil.copy(file, site_packages_dir)

# Navigate to the site-packages directory to zip the contents for AWS Lambda
shutil.make_archive("periscope", 'zip', site_packages_dir)

print("Packaging complete. The zip file is ready for deployment.")

# Move the zip file to a desired location (e.g., project root)
shutil.move("periscope.zip", os.path.join(os.getcwd(), "periscope.zip"))

# Note: Cleanup of the virtual environment (venv_dir) is optional.
