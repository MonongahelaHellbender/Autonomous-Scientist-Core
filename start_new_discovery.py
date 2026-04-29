import os
import sys

def setup_project(name):
    folders = [
        f"{name}/ingestion",
        f"{name}/intelligence",
        f"{name}/adversarial",
        f"{name}/economics"
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        with open(f"{folder}/.keep", "w") as f: pass
    
    print(f"SUCCESS: Universal Lab Structure created for project: '{name}'")
    print("Next Steps: 1. Add your API calls to /ingestion. 2. Add your AI model to /intelligence.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        setup_project(sys.argv[1])
    else:
        print("Usage: python3 start_new_discovery.py [project_name]")
