from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ApiSource:
    name: str
    url: str
    success_code: int
    unavailable_code: int
    enabled: bool

    def build_url(self, appid: str) -> str:
        return self.url.replace("<appid>", appid).replace("{appid}", appid)


class ApiRegistry:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def load_all(self) -> list[ApiSource]:
        if not self.file_path.exists():
            raise FileNotFoundError(f"api.json tidak ditemukan: {self.file_path}")

        content = json.loads(self.file_path.read_text(encoding="utf-8"))
        raw_list = content.get("api_list", [])
        if not isinstance(raw_list, list) or not raw_list:
            raise ValueError("api_list pada api.json kosong atau tidak valid")

        result: list[ApiSource] = []
        for item in raw_list:
            result.append(
                ApiSource(
                    name=str(item.get("name", "")).strip(),
                    url=str(item.get("url", "")).strip(),
                    success_code=int(item.get("success_code", 200)),
                    unavailable_code=int(item.get("unavailable_code", 404)),
                    enabled=bool(item.get("enabled", True)),
                )
            )
        return result

    def load_enabled(self) -> list[ApiSource]:
        sources = [x for x in self.load_all() if x.enabled]
        if not sources:
            raise ValueError("Tidak ada API aktif (enabled=true) di api.json")
        return sources

    def get_by_name(self, name: str) -> ApiSource:
        for source in self.load_enabled():
            if source.name.lower() == name.lower():
                return source
        raise ValueError(f"API '{name}' tidak ditemukan atau tidak aktif")
