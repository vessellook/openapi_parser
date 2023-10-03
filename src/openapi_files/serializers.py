import copy
import json

import yaml
from rest_framework import serializers
from rest_framework.exceptions import ParseError

from openapi_files import models, schemas


class OperationSerializer(serializers.Serializer):
    path = serializers.CharField()
    method = serializers.CharField()
    operationId = serializers.CharField()
    summary = serializers.CharField()
    description = serializers.CharField()


class OpenapiFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OpenapiFile
        fields = ["name", "schema_file", "created_at", "operations"]
        extra_kwargs = {
            "name": {"required": False},
            "created_at": {"read_only": True},
        }

    operations = OperationSerializer(many=True, read_only=True)
    schema_file = serializers.FileField(write_only=True)

    def create(self, validated_data):
        schema_file = validated_data["schema_file"]
        name = validated_data.get("name", schema_file.name)
        if schema_file.size > 100 * 1024:  # maximum size is 100 kb
            raise ParseError("Too big file")
        file_content = schema_file.read()
        try:
            schema = json.loads(file_content)
        except json.JSONDecodeError:
            try:
                schema = yaml.load(file_content)
            except yaml.YAMLError:
                raise ParseError("Bad file format")
        if not schemas.validate_openapi(schema):
            raise ParseError("Bad openapi schema")
        return models.OpenapiFile.objects.create(
            name=name,
            schema=schema,
        )


class OpenapiFileExtractSerializer(serializers.Serializer):
    class Meta:
        model = models.OpenapiFile
        fields = ["new_name", "operation_ids"]

    new_name = serializers.CharField()
    operation_ids = serializers.ListField(
        write_only=True,
        child=serializers.CharField(),
        allow_empty=True,
    )

    def validate(self, attrs):
        parent_file: models.OpenapiFile = self.context.get("parent_file")
        if not parent_file:
            raise serializers.ValidationError(
                detail="parent_file should be passed to serializer",
                code="context_error",
            )
        operations = parent_file.operations
        available_operation_ids = {o["operationId"] for o in operations}
        bad_operation_ids = []
        for operation_id in attrs["operation_ids"]:
            if operation_id not in available_operation_ids:
                bad_operation_ids.append(operation_id)
        if len(bad_operation_ids) > 0:
            raise serializers.ValidationError(
                detail=f"operations with ids {bad_operation_ids} don't exist",
            )
        return attrs

    def create(self, validated_data):
        parent_file: models.OpenapiFile = self.context["parent_file"]
        parent_operations = parent_file.operations
        operations_dict = {o["operationId"]: o for o in parent_operations}
        new_paths_obj = {}
        for operation_id in validated_data["operation_ids"]:
            operation = operations_dict[operation_id]
            path = operation.pop("path")
            method = operation.pop("method")
            pathitem_obj = new_paths_obj.setdefault(path, {})
            pathitem_obj[method] = operation
        if self.context.get("forbid_schema_pollution", False):
            schema = copy.deepcopy(parent_file.schema)
        else:
            schema = parent_file.schema
        schema["paths"] = new_paths_obj
        return models.OpenapiFile.objects.create(
            name=validated_data["new_name"],
            schema=schema,
        )


class OpenapiFileShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OpenapiFile
        fields = ["name", "created_at"]
