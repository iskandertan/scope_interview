"""Lease endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/leases", tags=["leases"])
