from dataclasses import dataclass


@dataclass
class UserStat:
    username: str
    count: int
