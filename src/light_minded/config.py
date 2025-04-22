import json
from pathlib import Path

def run():
    config = {
        "analysis_type": "CBMA",
        "dataset": "neurosynth",
        "atlas": "MNI152",
        "keyword": "emotion"  # example placeholder
    }

    config_path = Path("config/settings.json")
    config_path.parent.mkdir(exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

    print(f"Config saved to {config_path.resolve()}")

    # TODO: prompt user for inputs or to change defaults
    #  prompt user for online or offline mode
    #  add output dir

    #TODO: expand and connect to additional analysis options, applied in light_minded.py

