from django.contrib import admin
from .models import MasterItem, MasterUpload

@admin.register(MasterItem)
class MasterItemAdmin(admin.ModelAdmin):
    list_display = ('code','name','category','price','unit')
    search_fields = ('code','name')
    list_filter = ('category',)

@admin.register(MasterUpload)
class MasterUploadAdmin(admin.ModelAdmin):
    list_display = ('filename','filetype','uploaded_at','total_rows','notes')
    search_fields = ('filename',)
