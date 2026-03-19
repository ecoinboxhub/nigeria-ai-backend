import os
import re
import logging
from pathlib import Path
from typing import Any

os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
import chromadb
from chromadb.config import Settings as ChromaClientSettings
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings

logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)

try:
    import posthog

    _orig_capture = posthog.capture

    def _capture_compat(*args, **kwargs):
        # Chroma <=0.5 may call capture(distinct_id, event, properties).
        if len(args) >= 2:
            distinct_id = args[0]
            event = args[1]
            properties = args[2] if len(args) > 2 and isinstance(args[2], dict) else {}
            kwargs.setdefault("distinct_id", distinct_id)
            kwargs.setdefault("properties", properties)
            return _orig_capture(event, **kwargs)
        if len(args) == 1:
            return _orig_capture(args[0], **kwargs)
        event = kwargs.pop("event", "chroma_event")
        return _orig_capture(event, **kwargs)

    posthog.capture = _capture_compat
except Exception:
    pass

PROMPT_TEMPLATE = """Context: {context}

Log: {log_text}
Weather: {rainfall_mm}mm, {temperature_c}°C, {wind_speed_kmh}km/h

Analyze for safety hazards and risks."""

SAFETY_PROMPT = PromptTemplate(
    template=PROMPT_TEMPLATE,
    input_variables=["context", "log_text", "rainfall_mm", "temperature_c", "wind_speed_kmh"],
)

_CHROMA_CLIENTS: dict[str, chromadb.ClientAPI] = {}


def _embedding_model():
    if settings.openai_api_key:
        return OpenAIEmbeddings(api_key=settings.openai_api_key)
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def load_documents(pdf_paths: list[str], web_urls: list[str]) -> list[Any]:
    docs = []
    for p in pdf_paths:
        path = Path(p)
        if path.exists():
            docs.extend(PyPDFLoader(str(path)).load())
    for u in web_urls:
        try:
            docs.extend(WebBaseLoader(u).load())
        except Exception:
            continue
    return docs


def get_vectorstore(persist_dir: str, collection_name: str) -> Chroma:
    resolved_dir = str(Path(persist_dir).resolve())
    client = _CHROMA_CLIENTS.get(resolved_dir)
    if client is None:
        client = chromadb.PersistentClient(
            path=resolved_dir,
            settings=ChromaClientSettings(anonymized_telemetry=False),
        )
        _CHROMA_CLIENTS[resolved_dir] = client

    return Chroma(
        collection_name=collection_name,
        embedding_function=_embedding_model(),
        persist_directory=resolved_dir,
        client=client,
    )


def _extract_number(pattern: str, text: str, default: float = 0.0) -> float:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return default
    try:
        return float(match.group(1))
    except (TypeError, ValueError):
        return default


class _SafetyRetrievalAdapter:
    def __init__(self, qa_chain: RetrievalQA, retriever: Any, prompt: PromptTemplate):
        self.qa_chain = qa_chain
        self.retriever = retriever
        self.prompt = prompt

    def invoke(self, inputs: dict[str, Any]) -> dict[str, str]:
        # Backward-compatible path: callers that still send {"query": "..."}.
        if "query" in inputs and "log_text" in self.prompt.input_variables:
            query = str(inputs.get("query", ""))
            docs = self.retriever.invoke(query)
            context = "\n\n".join(getattr(doc, "page_content", "") for doc in docs)

            payload = {
                "context": context,
                "log_text": query,
                "rainfall_mm": _extract_number(r"rainfall:\s*([0-9]+(?:\.[0-9]+)?)", query, 0.0),
                "temperature_c": _extract_number(r"temperature:\s*([0-9]+(?:\.[0-9]+)?)", query, 0.0),
                "wind_speed_kmh": _extract_number(r"wind:\s*([0-9]+(?:\.[0-9]+)?)", query, 0.0),
            }
            result = self.qa_chain.combine_documents_chain.llm_chain.predict(**payload)
            return {"result": str(result)}

        return self.qa_chain.invoke(inputs)


def get_llm_chain(prompt: PromptTemplate, vectorstore: Chroma, k: int = 5) -> Any:
    if not isinstance(prompt, PromptTemplate):
        raise TypeError("get_llm_chain expects a PromptTemplate instance.")

    llm = OllamaLLM(model="mistral")
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},
    )
    return _SafetyRetrievalAdapter(qa_chain=qa_chain, retriever=retriever, prompt=prompt)
