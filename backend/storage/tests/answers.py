import json
import os

BASE_DIR = os.path.dirname(__file__)

FILE = os.path.join(
    BASE_DIR,
    "results.json"
)

if os.path.exists(FILE):

    with open(FILE, "r") as f:

        TEST_SUBMISSIONS = json.load(f)

else:

    TEST_SUBMISSIONS = {}