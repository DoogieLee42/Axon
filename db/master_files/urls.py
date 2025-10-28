from django.urls import path
from . import views, apis

urlpatterns = [
    path('upload/', views.upload_master_page, name='master_upload_page'),
    path('import/', apis.import_master_api, name='master_import_api'),   # ✅ apis로 변경
]
