from fastapi import APIRouter
from pydantic import BaseModel

from app.clause_types import CLAUSE_TYPE_LABELS, ClauseType

router = APIRouter(prefix="/clause-types", tags=["clause-types"])


class ClauseTypeOption(BaseModel):
    value: ClauseType
    label: str


@router.get("", response_model=list[ClauseTypeOption])
def list_clause_types() -> list[ClauseTypeOption]:
    return [ClauseTypeOption(value=ct, label=label) for ct, label in CLAUSE_TYPE_LABELS.items()]
