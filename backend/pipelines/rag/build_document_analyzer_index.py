import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.services.rag.index_builder import build_index


def main() -> None:
    build_index(
        name="document_analyzer",
        persist_subdir="document_analyzer",
        pdf_paths=[
            "data/raw/docs/NBC_2023.pdf",
            "data/raw/docs/COREN_Act_2018.pdf",
            "data/raw/docs/FIDIC_Red_Book.pdf",
            "data/raw/docs/FIDIC_Yellow_Book.pdf",
            "data/raw/docs/ILO_safety.pdf",
        ],
        web_urls=[
            "https://nigerianlawguru.com",
            "https://nigerianlawyerscenter.com",
            "https://etenders.com.ng",
        ],
    )
    print("Document analyzer index built")


if __name__ == "__main__":
    main()
