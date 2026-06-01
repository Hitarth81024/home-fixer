import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "home_fixer.settings")
django.setup()

from django.db import connection

def run_fix():
    cursor = connection.cursor()
    print("Executing ALTER TABLE to drop NOT NULL constraint on is_available column...")
    cursor.execute("ALTER TABLE home_booking ALTER COLUMN is_available DROP NOT NULL;")
    cursor.execute("ALTER TABLE home_booking ALTER COLUMN is_available SET DEFAULT TRUE;")
    print("Constraint updated successfully!")

if __name__ == "__main__":
    run_fix()
