import shutil
import os
import subprocess

# Specify your FastAPI application files here
app_files = ["main.py", ".env", "requirements.txt"]  # Add other necessary files
# Additional files Elastic Beanstalk might need
additional_files = ["Procfile"]

# Setup directory name for the Elastic Beanstalk deployment package
eb_package_dir = "eb_package"

# Create the deployment package directory if it doesn't exist
os.makedirs(eb_package_dir, exist_ok=True)

# Copy application and additional files to the deployment package directory
for file in app_files + additional_files:
    shutil.copy(file, eb_package_dir)

# Check if a Procfile exists, if not, create one
procfile_path = os.path.join(eb_package_dir, "Procfile")
#if Procfile does not exist, create one
with open(procfile_path, 'w') as procfile:
    procfile.write("web: uvicorn main:app --host 0.0.0.0 --port 5000")
                     
# Navigate to the deployment package directory
os.chdir(eb_package_dir)

# Zip the contents for Elastic Beanstalk
shutil.make_archive("../eb_deployment_package", 'zip', ".")

print("Packaging complete. The zip file is ready for deployment to Elastic Beanstalk.")

# Note: Cleanup of the eb_package directory is optional after zipping.
