import json
import os

FILE="storage/tests/results.json"

if os.path.exists(FILE):

    with open(FILE,"r") as f:

        TEST_SUBMISSIONS=json.load(f)

else:

    TEST_SUBMISSIONS={}