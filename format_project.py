import os
import subprocess

# Define the directory path of your project
project_directory = "./src"

# Define the file extensions of Python scripts you want to format
python_file_extensions = [".py"]

# Function to format Python scripts using black
def format_python_scripts(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(tuple(python_file_extensions)):
                file_path = os.path.join(root, file)
                # Run black formatter on the Python script
                subprocess.run(["autopep8", file_path], check=False)
                
def lint_python_scripts(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                # Run flake8 linter on the Python script
                subprocess.run(["flake8", file_path], check=False)

def main():
    # Format Python scripts
    print("Formatting Python scripts...")
    format_python_scripts(project_directory)
    print("Formatting completed.")

    # Lint Python scripts
    print("\nLinting Python scripts...")
    lint_python_scripts(project_directory)
    print("Linting completed.")

if __name__ == "__main__":
    main()