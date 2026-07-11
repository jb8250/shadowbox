from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class WorkspaceStatus(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class PersistenceConfig:
    downloads: bool = False
    cookies: bool = False
    extensions: bool = False
    bookmarks: bool = False
    session: bool = False


@dataclass
class WorkspaceState:
    name: str
    status: WorkspaceStatus = WorkspaceStatus.STOPPED
    persistence: PersistenceConfig = field(default_factory=PersistenceConfig)
    tor_identity: Optional[str] = None
    browser_container: Optional[str] = None
    tor_container: Optional[str] = None
    volume_name: str = ""
