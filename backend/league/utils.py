from typing import Any, Dict

from django.http import HttpRequest

from .models import AuditLog


def log_action(*, user, action: str, entity_type: str, entity_id: str, details: Dict[str, Any] | None = None, request: HttpRequest | None = None):
    ip = None
    if request:
        ip = request.META.get("REMOTE_ADDR")
    AuditLog.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        details=details or {},
        ip_address=ip,
    )
