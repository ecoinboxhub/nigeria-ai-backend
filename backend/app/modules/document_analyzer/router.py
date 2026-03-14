from fastapi import APIRouter, Depends

from app.core.rbac import Role, require_role
from app.modules.document_analyzer.schemas import DocumentAnalysisResponse, DocumentInput
from app.modules.document_analyzer.service import analyze_document

router = APIRouter()


@router.post('/review', response_model=DocumentAnalysisResponse, dependencies=[Depends(require_role([Role.ADMIN, Role.LEGAL, Role.PM]))])
def analyze_document_endpoint(payload: DocumentInput) -> DocumentAnalysisResponse:
    return analyze_document(payload)
