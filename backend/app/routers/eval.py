from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.eval import EvalCaseSchema, EvalResultSchema, EvalRunResponse
from app.services.eval_service import list_eval_cases, list_eval_results, run_all_evals


router = APIRouter(prefix="/eval", tags=["eval"])


@router.get("/cases", response_model=list[EvalCaseSchema])
def get_eval_cases(db: Session = Depends(get_db)) -> list[EvalCaseSchema]:
    return [EvalCaseSchema.model_validate(case) for case in list_eval_cases(db)]


@router.post("/run", response_model=EvalRunResponse)
def run_evals(db: Session = Depends(get_db)) -> EvalRunResponse:
    results = [EvalResultSchema.model_validate(result) for result in run_all_evals(db)]
    return EvalRunResponse(total_cases=len(results), results=results)


@router.get("/results", response_model=list[EvalResultSchema])
def get_eval_results(db: Session = Depends(get_db)) -> list[EvalResultSchema]:
    return [EvalResultSchema.model_validate(result) for result in list_eval_results(db)]
