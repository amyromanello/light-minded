import json
from pathlib import Path
from src.light_minded import light_minded as lm

def run():
    config_path = Path("config/settings.json")
    if not config_path.exists():
        print("[!] No config found. Please run 'python main_caller.py config' first.")
        return

    with open(config_path) as f:
        config = json.load(f)

    print(f"Launching with config:\n{json.dumps(config, indent=4)}")

    lm.main()

    #TODO: test for online/offline requirements, atlas and dataset files
    # should all pass before core module runs

    #TODO: specifcy config file precedence. default settings file vs customized file (most recent one)


