"""Permission catalogue, role seeding, authorization checks (never check role names in GUI)."""
from __future__ import annotations

PERMISSIONS = [
    ("properties.view", "View properties"),
    ("properties.create", "Create properties"),
    ("properties.edit", "Edit properties"),
    ("properties.delete", "Delete/archive properties"),
    ("owners.view", "View owners"), ("owners.edit", "Edit owners"),
    ("clients.view", "View clients"), ("clients.edit", "Edit clients"),
    ("agents.view", "View agents"), ("agents.edit", "Edit agents"),
    ("visits.view", "View visits"), ("visits.edit", "Edit visits"),
    ("contracts.view", "View contracts"), ("contracts.create", "Create contracts"),
    ("contracts.edit", "Edit contracts"),
    ("payments.view", "View payments"), ("payments.edit", "Edit payments"),
    ("expenses.view", "View expenses"), ("expenses.edit", "Edit expenses"),
    ("documents.view", "View documents"), ("documents.edit", "Edit documents"),
    ("reports.view", "View/export reports"),
    ("users.manage", "Manage users"),
    ("roles.manage", "Manage roles/permissions"),
    ("backups.manage", "Manage backups"),
    ("audit.view", "View audit log"),
    ("settings.edit", "Edit settings"),
]

ROLE_PERMS: dict[str, list[str]] = {
    "ADMIN": [p for p, _ in PERMISSIONS],
    "MANAGER": [p for p, _ in PERMISSIONS if not p.startswith("users.") and not p.startswith("roles.")],
    "AGENT": ["properties.view", "properties.create", "properties.edit", "owners.view",
              "clients.view", "clients.edit", "agents.view", "visits.view", "visits.edit",
              "contracts.view", "documents.view", "documents.edit", "reports.view"],
    "ACCOUNTANT": ["properties.view", "owners.view", "clients.view", "contracts.view",
                   "payments.view", "payments.edit", "expenses.view", "expenses.edit",
                   "reports.view", "documents.view"],
    "VIEWER": ["properties.view", "owners.view", "clients.view", "agents.view",
               "visits.view", "contracts.view", "payments.view", "expenses.view",
               "documents.view", "reports.view"],
}


def user_permissions(user) -> set[str]:
    perms: set[str] = set()
    for r in (user.roles or []):
        for p in (r.permissions or []):
            perms.add(p.code)
    return perms


def has_permission(user, code: str) -> bool:
    if user is None:
        return False
    return code in user_permissions(user)


def require(user, code: str) -> None:
    if not has_permission(user, code):
        raise PermissionError(f"Permesso mancante: {code}")
