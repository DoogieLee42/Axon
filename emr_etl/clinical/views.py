from rest_framework import viewsets
from .models import Patient, Encounter, Diagnosis, Order
from .serializers import PatientSerializer, EncounterSerializer, DiagnosisSerializer, OrderSerializer

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().order_by('id')
    serializer_class = PatientSerializer

class EncounterViewSet(viewsets.ModelViewSet):
    queryset = Encounter.objects.all().order_by('-visited_at')
    serializer_class = EncounterSerializer

class DiagnosisViewSet(viewsets.ModelViewSet):
    queryset = Diagnosis.objects.all().order_by('id')
    serializer_class = DiagnosisSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('id')
    serializer_class = OrderSerializer
