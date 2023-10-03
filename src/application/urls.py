from django.contrib import admin
from django.urls import path
from rest_framework.routers import DefaultRouter

from openapi_files import views

router = DefaultRouter()
router.register("files", views.OpenapiFilesViewSet, basename="files")

urlpatterns = [
    path("admin/", admin.site.urls),
]

urlpatterns += router.get_urls()
