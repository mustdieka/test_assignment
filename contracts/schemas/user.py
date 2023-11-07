from enum import Enum, unique


@unique
class UserRole(str, Enum):
    WORKER = "WORKER"
    MANAGER = "MANAGER"
