import logging
from pathlib import Path

from langchain.prompts import PromptTemplate

from app.core.config import settings
from app.modules.document_analyzer.schemas import ClauseExtraction, DocumentAnalysisResponse, DocumentInput
from app.services.rag.engine import get_llm_chain, get_vectorstore
from app.utils.security_utils import mask_pii, sanitize_input_text

logger = logging.getLogger(__name__)

REQUIRED_CLAUSES = {
    "payment terms": "Define payment timelines and milestones.",
    "variation": "Change-order process must be explicit.",
    "termination": "Termination conditions required under local practice.",
    "dispute resolution": "Arbitration or litigation path is required.",
    "health and safety": "Must align with COREN Act 2018 obligations.",
}

PROMPT_TEMPLATE = (
    "Given the following Nigerian construction regulations and contract clauses, analyze the document and identify: "
    "(1) compliance issues, (2) missing clauses, (3) risk factors. "
    "Document: {context}. Query: {question}"
)
DOCUMENT_PROMPT = PromptTemplate.from_template(PROMPT_TEMPLATE)


def _rag_assist(document_text: str) -> str:
    try:
        persist_dir = Path(settings.chroma_persist_dir) / "document_analyzer"
        persist_dir.mkdir(parents=True, exist_ok=True)
        vectordb = get_vectorstore(str(persist_dir), collection_name="document_analyzer")
        chain = get_llm_chain(DOCUMENT_PROMPT, vectordb, k=5)
        out = chain.invoke({"query": document_text})
        if isinstance(out, dict):
            return str(out.get("result", ""))
        return str(out)
    except Exception as e:
        logger.error(f"RAG assistance failed in document_analyzer: {e}")
        return ""


def analyze_document(payload: DocumentInput) -> DocumentAnalysisResponse:
    safe_text = mask_pii(sanitize_input_text(payload.text.lower()))
    rag_context = _rag_assist(safe_text)

    clauses: list[ClauseExtraction] = []
    present_count = 0
    for clause, recommendation in REQUIRED_CLAUSES.items():
        present = clause in safe_text
        if present:
            present_count += 1
        comment = "Found" if present else recommendation
        if rag_context:
            comment = f"{comment} | RAG: {rag_context[:120]}"
        clauses.append(
            ClauseExtraction(
                clause=clause,
                present=present,
                comment=comment,
                confidence=0.9 if present else 0.72,
            )
        )

    score = round((present_count / len(REQUIRED_CLAUSES)) * 100, 2)
    return DocumentAnalysisResponse(title=payload.title, clauses=clauses, compliance_score=score)
