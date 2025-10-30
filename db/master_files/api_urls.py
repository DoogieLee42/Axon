from django.urls import path

from . import api_views

app_name = "master_files_api"

urlpatterns = [
    path("items/", api_views.MasterItemCollectionView.as_view(), name="items"),
    path("items/<int:pk>/", api_views.MasterItemDetailView.as_view(), name="item-detail"),
    path("uploads/", api_views.MasterUploadCollectionView.as_view(), name="uploads"),
    path("uploads/<int:pk>/", api_views.MasterUploadDetailView.as_view(), name="upload-detail"),
]
