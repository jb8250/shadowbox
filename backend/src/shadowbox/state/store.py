from typing import Optional

from shadowbox.state.models import WorkspaceState, WorkspaceStatus, PersistenceConfig


class StateStore:
    def __init__(self) -> None:
        self._workspaces: dict[str, WorkspaceState] = {}

    def create(self, name: str) -> WorkspaceState:
        state = WorkspaceState(
            name=name,
            volume_name=f"shadowbox-{name}",
        )
        self._workspaces[name] = state
        return state

    def get(self, name: str) -> Optional[WorkspaceState]:
        return self._workspaces.get(name)

    def set_status(self, name: str, status: WorkspaceStatus) -> WorkspaceState:
        ws = self._workspaces[name]
        ws.status = status
        return ws

    def ensure(self, name: str) -> WorkspaceState:
        if name not in self._workspaces:
            return self.create(name)
        return self._workspaces[name]


store = StateStore()
