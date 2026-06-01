import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "home_fixer.settings")
django.setup()

from django.db import connection

def inspect_table():
    cursor = connection.cursor()
    cursor.execute("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'home_booking'")
    rows = cursor.fetchall()
    print("Columns in home_booking table:")
    for row in rows:
        print(f" - {row[0]} ({row[1]}), Nullable: {row[2]}")

if __name__ == "__main__":
    inspect_table()
