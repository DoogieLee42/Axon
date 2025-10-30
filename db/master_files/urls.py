from django.urls import path

from . import views
from .api_views import MasterUploadCollectionView

app_name = "master_files"

urlpatterns = [
    path("upload/", views.upload_master_page, name="master_upload_page"),
    # Keep legacy endpoint for the upload form while new REST URLs live under /api/master/.
    path("import/", MasterUploadCollectionView.as_view(), name="master_import_api"),
]
