"""Documentation parser for extracting deck-relevant project narrative."""

from __future__ import annotations

import re
from pathlib import Path


class DocumentParser:
    """Parse README and optional docs with explicit warning collection."""

    README_CANDIDATES = ["README.md", "readme.md", "README.txt", "README"]

    PROBLEM_HEADERS = {"problem", "challenge", "pain point", "motivation", "issue"}
    SOLUTION_HEADERS = {"solution", "approach", "how it works", "architecture"}
    FEATURE_HEADERS = {"features", "capabilities", "functionality", "highlights"}
    IMPACT_HEADERS = {"impact", "benefits", "value", "outcomes"}
    FUTURE_HEADERS = {"future", "roadmap", "next steps", "future work"}
    INSTALL_HEADERS = {"installation", "setup", "getting started"}
    USAGE_HEADERS = {"usage", "examples", "how to use"}

    def __init__(self, project_path: Path | str, additional_docs: list[str] | None = None):
        self.project_path = Path(project_path).resolve()
        self.additional_docs = list(additional_docs or [])
        self.warnings: list[str] = []

    def parse(self) -> dict:
        doc = {
            "title": self.project_path.name,
            "description": "",
            "problem": "",
            "solution": "",
            "features": [],
            "impact_points": [],
            "future_items": [],
            "installation": "",
            "usage": "",
            "warnings": self.warnings,
        }

        readme = self._find_readme()
        if readme:
            self._parse_markdown_file(readme, doc, is_readme=True)
        else:
            self.warnings.append("README file not found; using fallback metadata.")

        for raw_path in self.additional_docs:
            self._parse_additional_doc(raw_path, doc)

        return doc

    def _find_readme(self) -> Path | None:
        for name in self.README_CANDIDATES:
            path = self.project_path / name
            if path.exists() and path.is_file():
                return path
        return None

    def _parse_markdown_file(self, path: Path, doc: dict, is_readme: bool = False) -> None:
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            self.warnings.append(f"Failed to read {path}: {exc}")
            return

        title, sections, intro = self._split_sections(content)

        if is_readme and title:
            doc["title"] = title

        if intro and not doc["description"]:
            doc["description"] = intro[:500]

        for header, section_text in sections.items():
            key = header.lower().strip()
            normalized = re.sub(r"[^a-z0-9 ]+", "", key)

            if normalized in self.PROBLEM_HEADERS and not doc["problem"]:
                doc["problem"] = section_text[:700]
            elif normalized in self.SOLUTION_HEADERS and not doc["solution"]:
                doc["solution"] = section_text[:700]
            elif normalized in self.FEATURE_HEADERS and not doc["features"]:
                doc["features"] = self._extract_list_items(section_text, limit=10)
            elif normalized in self.IMPACT_HEADERS and not doc["impact_points"]:
                doc["impact_points"] = self._extract_list_items(section_text, limit=8)
            elif normalized in self.FUTURE_HEADERS and not doc["future_items"]:
                doc["future_items"] = self._extract_list_items(section_text, limit=8)
            elif normalized in self.INSTALL_HEADERS and not doc["installation"]:
                doc["installation"] = section_text[:400]
            elif normalized in self.USAGE_HEADERS and not doc["usage"]:
                doc["usage"] = section_text[:400]

    def _parse_additional_doc(self, raw_path: str, doc: dict) -> None:
        candidate = Path(raw_path)
        path = candidate if candidate.is_absolute() else (self.project_path / candidate)
        path = path.resolve()

        if not path.exists() or not path.is_file():
            self.warnings.append(f"Additional doc not found: {raw_path}")
            return

        if not self._is_within_project(path):
            self.warnings.append(f"Skipped doc outside project directory: {path}")
            return

        if path.suffix.lower() in {".md", ".markdown", ".txt", ".rst"}:
            self._parse_markdown_file(path, doc, is_readme=False)
        else:
            try:
                snippet = path.read_text(encoding="utf-8", errors="ignore")[:300]
            except OSError as exc:
                self.warnings.append(f"Failed to read additional doc {path}: {exc}")
                return
            if snippet and len(doc.get("description", "")) < 700:
                joined = f"{doc.get('description', '').strip()}\n\n{snippet}".strip()
                doc["description"] = joined[:700]

    def _is_within_project(self, path: Path) -> bool:
        try:
            path.relative_to(self.project_path)
            return True
        except ValueError:
            return False

    def _split_sections(self, content: str) -> tuple[str, dict[str, str], str]:
        lines = content.splitlines()
        sections: dict[str, list[str]] = {}

        title = ""
        current_header = ""
        intro_lines: list[str] = []
        saw_section = False

        header_pattern = re.compile(r"^(#{1,3})\s+(.+?)\s*$")

        for line in lines:
            match = header_pattern.match(line)
            if match:
                level = len(match.group(1))
                header = match.group(2).strip()

                if level == 1 and not title:
                    title = header
                    current_header = ""
                    continue

                saw_section = True
                current_header = header
                sections.setdefault(current_header, [])
                continue

            if current_header:
                sections[current_header].append(line)
            elif not saw_section:
                intro_lines.append(line)

        finalized = {
            header: self._cleanup_section("\n".join(value))
            for header, value in sections.items()
            if self._cleanup_section("\n".join(value))
        }

        intro = self._cleanup_section("\n".join(intro_lines))
        return title, finalized, intro

    def _cleanup_section(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    def _extract_list_items(self, text: str, limit: int = 8) -> list[str]:
        items: list[str] = []

        bullet_pattern = re.compile(r"^\s*(?:[-*]|\d+\.)\s+(.+?)\s*$")
        for line in text.splitlines():
            match = bullet_pattern.match(line)
            if match:
                item = match.group(1).strip()
                if item:
                    items.append(item)

        if not items:
            sentences = [seg.strip() for seg in re.split(r"[\n\.]", text) if seg.strip()]
            items = sentences[:limit]

        unique: list[str] = []
        seen = set()
        for item in items:
            lowered = item.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            unique.append(item)
            if len(unique) >= limit:
                break

        return unique
