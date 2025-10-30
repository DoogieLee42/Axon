from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from clinical.views import PatientViewSet, EncounterViewSet, DiagnosisViewSet, OrderViewSet

router = DefaultRouter()
router.register(r'patients', PatientViewSet)
router.register(r'encounters', EncounterViewSet)
router.register(r'diagnoses', DiagnosisViewSet)
router.register(r'orders', OrderViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
