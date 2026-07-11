from pathlib import Path


class VaultManager:
    def __init__(self, workspace_name: str) -> None:
        base = Path.home() / ".shadowbox" / "vaults" / workspace_name
        self.path = base
        self.path.mkdir(parents=True, exist_ok=True)

    def usage_bytes(self) -> int:
        total = 0
        for child in self.path.rglob("*"):
            if child.is_file():
                total += child.stat().st_size
        return total

    def destroy(self) -> None:
        import shutil
        shutil.rmtree(self.path, ignore_errors=True)
