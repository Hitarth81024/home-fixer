import os
import sys
import django
import json

# Set up Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "home_fixer.settings")
django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from rest_framework.test import APIClient

def update_swagger():
    client = APIClient()
    response = client.get("/swagger.json")
    if response.status_code == 200:
        data = response.json()
        output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../swagger_temp.json"))
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("Successfully updated swagger_temp.json!")
    else:
        print(f"Failed to fetch swagger.json: HTTP {response.status_code}")
        print(response.content[:200])

if __name__ == "__main__":
    update_swagger()
