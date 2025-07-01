import os
import yaml

with open(os.path.join("data", "names.yml")) as fh:
    data = yaml.safe_load(fh)

FIRST_NAMES = data.get("first_names", [])
LAST_NAMES = data.get("last_names", [])
