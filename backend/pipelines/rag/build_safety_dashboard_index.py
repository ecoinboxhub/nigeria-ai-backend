import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.services.rag.index_builder import build_index


def main() -> None:
    build_index(
        name="safety_dashboard",
        persist_subdir="safety_dashboard",
        pdf_paths=[
            "data/raw/docs/ILO_safety.pdf",
            "data/raw/docs/COREN_Act_2018.pdf",
        ],
        web_urls=[
            "https://www.ilo.org/media/425186/download",
        ],
    )
    print("Safety dashboard index built")


if __name__ == "__main__":
    main()
