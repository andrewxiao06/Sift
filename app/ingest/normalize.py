"""Converts a raw arxiv.Result into the record shape stored in the papers table."""

import re

import arxiv

_VERSION_SUFFIX = re.compile(r"v\d+$")


def strip_version(arxiv_id: str) -> str:
    return _VERSION_SUFFIX.sub("", arxiv_id)


def normalize(result: arxiv.Result) -> dict:
    return {
        "arxiv_id": strip_version(result.get_short_id()),
        "title": result.title.strip(),
        "abstract": result.summary.strip(),
        "authors": [author.name for author in result.authors],
        "categories": list(result.categories),
        "published": result.published,
        "updated": result.updated,
        "pdf_url": result.pdf_url,
    }
