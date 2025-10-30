from django.contrib import admin
from .models import Patient, Encounter, Diagnosis, Order
admin.site.register([Patient, Encounter, Diagnosis, Order])
