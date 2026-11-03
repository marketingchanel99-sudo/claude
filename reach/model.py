"""모든 소스의 결과를 담는 공통 모양."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class Post:
    source: str            # "reddit" | "youtube" | ...
    title: str
    url: str
    community: str = ""    # 서브레딧 이름, 유튜브 채널 이름 등
    text: str = ""
    score: int = 0         # 추천 수 / 조회 수 같은 반응 지표
    comments: int = 0
    published_at: Optional[str] = None  # ISO 8601
    query: str = ""        # 어떤 검색어로 찾았는지
    backend: str = ""      # 실제로 가져온 백엔드

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Post":
        names = cls.__dataclass_fields__
        return cls(**{k: v for k, v in d.items() if k in names})


@dataclass
class Attempt:
    """백엔드 하나를 시도한 기록. 리포트에 그대로 남긴다."""
    source: str
    backend: str
    query: str
    ok: bool
    count: int = 0
    error: str = ""


@dataclass
class Collection:
    posts: list = field(default_factory=list)
    attempts: list = field(default_factory=list)
