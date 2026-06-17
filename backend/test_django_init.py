import os
import sys
import django
import logging
import traceback

# Enable verbose logging
logging.basicConfig(level=logging.DEBUG)

print("1. Setting DJANGO_SETTINGS_MODULE...")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smartpark.settings")

print("2. Calling django.setup()...")
django.setup()
print("django.setup() completed successfully!")

print("3. Querying ParkingLot model...")
from apps.parking.models import ParkingLot
try:
    lot = ParkingLot.objects.first()
    print(f"Query completed! First lot: {lot}")
except Exception as e:
    print("Query failed!")
    traceback.print_exc()
