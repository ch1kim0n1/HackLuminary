"""Image indexer tests for v2.2 visual pipeline."""

from __future__ import annotations

import base64

from hackluminary.image_indexer import index_project_images


_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)


def test_indexer_discovers_images_and_markdown_refs(tmp_path):
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "demo-screen.png").write_bytes(_PNG_1X1)

    (tmp_path / "README.md").write_text(
        "# Demo\n\n![UI screenshot](assets/demo-screen.png)\n",
        encoding="utf-8",
    )

    indexed = index_project_images(
        project_root=tmp_path,
        image_dirs=[],
        allowed_extensions=[".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"],
        max_image_bytes=3_145_728,
    )

    assert indexed["summary"]["count"] == 1
    media = indexed["media_catalog"][0]
    assert media["source_path"] == "assets/demo-screen.png"
    assert media["kind"] == "doc_image"
    assert media["mime"] == "image/png"
    assert media["width"] == 1
    assert media["height"] == 1
    assert len(media["sha256"]) == 64
    assert "ui" in media["tags"]


def test_indexer_rejects_outside_project_dirs(tmp_path):
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")

    indexed = index_project_images(
        project_root=tmp_path,
        image_dirs=["../"],
        allowed_extensions=[".png"],
        max_image_bytes=3_145_728,
    )

    assert indexed["summary"]["count"] == 0
    assert any("outside project root" in warning.lower() for warning in indexed["warnings"])
