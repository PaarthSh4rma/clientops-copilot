"""Upload provider credentials to the linked Vercel project without logging values."""

import subprocess
from pathlib import Path

from app.core.config import Settings


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    settings = Settings(_env_file=root / "backend" / ".env")
    secrets = {
        "PINECONE_API_KEY": settings.pinecone_api_key,
        "OPENROUTER_API_KEY": settings.openrouter_api_key,
    }
    if any(not value for value in secrets.values()):
        raise RuntimeError("Both provider keys must be configured in backend/.env")
    for name, value in secrets.items():
        result = subprocess.run(
            [
                "npx",
                "--yes",
                "vercel@65.3.1",
                "env",
                "add",
                name,
                "--environment",
                "production",
                "--sensitive",
                "--force",
                "--yes",
                "--cwd",
                str(root),
            ],
            input=value,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(f"Could not configure {name}; use the Vercel environment settings")
        print(f"Configured {name} as a production secret")


if __name__ == "__main__":
    main()
