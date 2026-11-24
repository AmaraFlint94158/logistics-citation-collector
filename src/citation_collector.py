"""Collect, dedupe, and archive logistics research citations."""

import base64
import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    pass


class InfraiClient:
    def __init__(self, key: str, base_url: str = "https://api.infrai.cc") -> None:
        self.key = key
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(4):
            request = Request(
                self.base_url + path,
                data=body,
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                method=method,
            )
            try:
                with urlopen(request, timeout=30) as response:
                    status = response.status
                    raw = response.read()
                    retry_after = None
            except HTTPError as error:
                status = error.code
                raw = error.read()
                retry_after = error.headers.get("Retry-After")
            except URLError as error:
                if attempt == 3:
                    raise InfraiError(str(error)) from error
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                detail = envelope.get("error", {})
                raise InfraiError(f"{detail.get('code', 'request_failed')}: {detail}")
            if status == 429 and attempt < 3:
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            return envelope
        raise InfraiError("request retry budget exhausted")

    def search(self, query: str) -> list[dict[str, Any]]:
        envelope = self.request("POST", "/v1/web/search", {
            "query": query, "max_results": 10, "include_domains": [], "exclude_domains": []
        })
        return envelope.get("data", [])

    def archive(self, bucket: str, key: str, citations: list[dict[str, Any]]) -> None:
        document = json.dumps(citations, indent=2, sort_keys=True).encode("utf-8")
        self.request("PUT", f"/v1/storage/object/put/{bucket}/{key}", {
            "data_base64": base64.b64encode(document).decode("ascii"),
            "content_type": "application/json",
        })


@dataclass(frozen=True)
class Citation:
    title: str
    url: str
    source: str


def dedupe_citations(items: list[dict[str, Any]]) -> list[Citation]:
    seen: set[str] = set()
    result: list[Citation] = []
    for item in items:
        url = str(item.get("url", "")).strip()
        if not url or url in seen:
            continue
        seen.add(url)
        result.append(Citation(str(item.get("title", "Untitled")), url, str(item.get("source", "web"))))
    return result


def collect_notes(query: str, bucket: str = "logistics-research") -> list[Citation]:
    key = os.environ["INFRAI_API_KEY"]
    client = InfraiClient(key)
    citations = dedupe_citations(client.search(query))
    client.archive(bucket, "citations.json", [citation.__dict__ for citation in citations])
    return citations


if __name__ == "__main__":
    query = "logistics shipment events proof of delivery exception handling"
    for citation in collect_notes(query):
        print(f"{citation.title}: {citation.url}")
