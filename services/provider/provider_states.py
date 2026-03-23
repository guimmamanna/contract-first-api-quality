"""
Provider state handler for Pact verification.

These endpoints are only used during contract verification to set up the
provider's internal state to match the "given" clauses in the Pact file.
"""

from fastapi import APIRouter, Request
from services.provider.database import EmployeeStore

router = APIRouter(prefix="/_pact", tags=["Pact"])

# Shared reference — the app's store is passed in at startup
_store: EmployeeStore | None = None


def init_provider_states(store: EmployeeStore) -> APIRouter:
    global _store
    _store = store
    return router


@router.post("/provider-states")
async def provider_states(request: Request):
    """
    Pact calls this endpoint with { "state": "..." } before each interaction.
    We set up the in-memory store accordingly.
    """
    body = await request.json()
    state = body.get("state", "")

    if _store is None:
        return {"result": "error", "message": "store not initialised"}

    _store.reset()

    if "employees exist" in state.lower():
        pass  # seed data already present after reset

    if "no employee with id not-found-id exists" in state.lower():
        pass  # not-found-id is never in seed data

    if "no employee with email" in state.lower():
        email = state.split("no employee with email ")[-1].split(" ")[0]
        emp = _store.find_by_email(email)
        if emp:
            _store.delete(emp["id"])

    if "already exists" in state.lower() and "email" in state.lower():
        email = state.split("email ")[-1].split(" ")[0]
        if not _store.find_by_email(email):
            _store.create({
                "first_name": "Existing",
                "last_name": "User",
                "email": email,
                "job_title": "Placeholder",
                "department": "Engineering",
                "salary": 100000.0,
            })

    return {"result": "ok"}
