from typing import List, TypedDict

from django.db import models


class Operation(TypedDict):
    path: str
    method: str
    operation_id: str
    summary: str


class OpenapiFile(models.Model):
    name = models.CharField(max_length=511, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    schema = models.JSONField()

    @property
    def operations(self) -> List[Operation]:
        paths_obj = self.schema.get("paths")
        if not paths_obj:
            return []
        operations = []
        for path, pathitem_obj in paths_obj.items():
            for method, operation_obj in pathitem_obj.items():
                operation = {
                    "path": path,
                    "method": method,
                    **operation_obj,
                }
                operations.append(operation)
        return operations
