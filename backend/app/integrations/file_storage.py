from pathlib import Path


class LocalFileStorage:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, stored_filename: str) -> Path:
        return self.root / Path(stored_filename).name

    def write(self, stored_filename: str, content: bytes) -> Path:
        path = self.path_for(stored_filename)
        temporary = path.with_suffix(f"{path.suffix}.tmp")
        try:
            temporary.write_bytes(content)
            temporary.replace(path)
        except OSError:
            temporary.unlink(missing_ok=True)
            path.unlink(missing_ok=True)
            raise
        return path

    def delete(self, stored_filename: str) -> None:
        self.path_for(stored_filename).unlink(missing_ok=True)

    def ready(self) -> bool:
        try:
            probe = self.root / ".readiness"
            probe.touch()
            probe.unlink()
            return True
        except OSError:
            return False
