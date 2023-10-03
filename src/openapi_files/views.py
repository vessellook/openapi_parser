import json

import yaml
from django.http import HttpResponse
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response

from openapi_files import models, serializers, schemas


class OpenapiFilesViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet):
    queryset = models.OpenapiFile.objects.order_by("name")
    lookup_field = "name"
    parser_classes = [MultiPartParser, JSONParser]

    def get_serializer_class(self):
        print(self.action)
        if self.action == "list":
            return serializers.OpenapiFileShortSerializer
        if self.action in {"retrieve", "create"}:
            return serializers.OpenapiFileSerializer
        if self.action == "extract":
            return serializers.OpenapiFileExtractSerializer

    @action(detail=True, methods=["POST"])
    def extract(self, request, name: str):
        openapi_file = self.get_object()
        input_serializer = serializers.OpenapiFileExtractSerializer(
            data=request.data,
            context={"parent_file": openapi_file}
        )
        input_serializer.is_valid(raise_exception=True)
        instance = input_serializer.save()
        output_serializer = serializers.OpenapiFileSerializer(
            instance,
        )
        return Response(output_serializer.data)

    @action(detail=True, methods=["GET"])
    def file(self, request, name: str):
        output_format = request.query_params.get("output")
        openapi_file = self.get_object()
        print(openapi_file.schema.keys())
        if output_format == "yaml":
            content = yaml.dump(
                openapi_file.schema,
                encoding="UTF-8",
                sort_keys=False,
            )
            return HttpResponse(content, content_type="application/x-yaml")
        if output_format == "json" or output_format is None:
            return Response(openapi_file.schema)
        return ParseError(f"Unexpected output format {output_format}")
