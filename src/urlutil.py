"""URL の絶対化(T-003)とドメイン検査(G-03)。"""

from __future__ import annotations

from urllib.parse import urljoin, urlparse


def absolutize(base: str, href: str) -> str:
    return urljoin(base, href)


def in_domains(url: str, allowed: list[str]) -> bool:
    """https かつ、ホストが allowed のいずれかと一致またはそのサブドメインなら True。"""
    p = urlparse(url)
    if p.scheme != "https" or not p.hostname:
        return False
    host = p.hostname.lower()
    return any(host == d.lower() or host.endswith("." + d.lower()) for d in allowed)
