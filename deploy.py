import subprocess
import shutil
import os
import venv

# Specify your FastAPI application file (or files) here
app_files = ["main.py",'.env']  # Add other files as needed
requirements_file = "requirements.txt"  # Path to your requirements file

# Setup virtual environment directory name
venv_dir = "venv_lambda"

# Create virtual environment
venv.create(venv_dir, with_pip=True)

# Activate the virtual environment and install dependencies
pip_install_cmd = f"{venv_dir}/bin/pip install -r {requirements_file}"
subprocess.run(pip_install_cmd, shell=True, check=True)

# Install additional dependencies required by AWS Lambda & FastAPI
additional_packages = ["fastapi", "uvicorn", "mangum"]
subprocess.run([f"{venv_dir}/bin/pip", "install"] + additional_packages, check=True)

# Path to the site-packages directory where dependencies are installed
site_packages_dir = os.path.join(venv_dir, "lib", subprocess.check_output([f"{venv_dir}/bin/python", "-c", "import site; print(site.getsitepackages()[0])"]).decode().strip())

# Create a /temp_images directory inside the package
temp_images_dir = os.path.join(site_packages_dir, "temp_images")
os.makedirs(temp_images_dir, exist_ok=True)

# Optionally, copy any static files to the /temp_images directory here
# Example: shutil.copy('path/to/static/image.jpg', temp_images_dir)

# Copy app files to the site-packages directory
for file in app_files:
    shutil.copy(file, site_packages_dir)

# Zip the entire virtual environment site-packages for AWS Lambda
shutil.make_archive("my_fastapi_app", 'zip', site_packages_dir)

print("Packaging complete. The zip file is ready for deployment.")

# Note: Cleanup of the virtual environment (venv_dir) is optional.
