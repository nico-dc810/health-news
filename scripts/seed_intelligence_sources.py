import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.services.intelligence_center import seed_intelligence_sources


def main() -> None:
    with SessionLocal() as db:
        sources = seed_intelligence_sources(db, workspace_id="demo-workspace")
        print(f"seeded {len(sources)} intelligence sources")
        for source in sources:
            print(f"- {source.name} [{source.category}] {source.url}")


if __name__ == "__main__":
    main()
