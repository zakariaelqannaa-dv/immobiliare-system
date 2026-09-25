"""Minimal i18n: Italian default, English fallback. No UI text in business logic core."""
from __future__ import annotations

STRINGS = {
    "it": {
        "app_title": "Immobiliare System",
        "login": "Accedi",
        "username": "Nome utente o email",
        "password": "Password",
        "dashboard": "Cruscotto",
        "properties": "Immobili",
        "owners": "Proprietari",
        "clients": "Clienti",
        "agents": "Agenti",
        "visits": "Visite",
        "appointments": "Appuntamenti",
        "contracts": "Contratti",
        "rentals": "Locazioni",
        "sales": "Vendite",
        "payments": "Pagamenti",
        "expenses": "Spese",
        "documents": "Documenti",
        "tasks": "Attività",
        "calendar": "Calendario",
        "reports": "Report",
        "notifications": "Notifiche",
        "users": "Utenti",
        "audit": "Registro audit",
        "backup": "Backup",
        "settings": "Impostazioni",
        "search": "Cerca",
        "new": "Nuovo",
        "edit": "Modifica",
        "delete": "Elimina",
        "save": "Salva",
        "cancel": "Annulla",
        "confirm_delete": "Confermi l'eliminazione?",
        "logout": "Esci",
    },
    "en": {
        "app_title": "Immobiliare System",
        "login": "Sign in",
        "username": "Username or email",
        "password": "Password",
        "dashboard": "Dashboard",
        "properties": "Properties",
        "owners": "Owners",
        "clients": "Clients",
        "agents": "Agents",
        "visits": "Visits",
        "appointments": "Appointments",
        "contracts": "Contracts",
        "rentals": "Rentals",
        "sales": "Sales",
        "payments": "Payments",
        "expenses": "Expenses",
        "documents": "Documents",
        "tasks": "Tasks",
        "calendar": "Calendar",
        "reports": "Reports",
        "notifications": "Notifications",
        "users": "Users",
        "audit": "Audit log",
        "backup": "Backup",
        "settings": "Settings",
        "search": "Search",
        "new": "New",
        "edit": "Edit",
        "delete": "Delete",
        "save": "Save",
        "cancel": "Cancel",
        "confirm_delete": "Confirm deletion?",
        "logout": "Logout",
    },
}

_current = "it"


def set_language(code: str) -> None:
    global _current
    if code in STRINGS:
        _current = code


def t(key: str) -> str:
    return STRINGS.get(_current, {}).get(key) or STRINGS["en"].get(key, key)
