"""Deterministic codebase analyzer for HackLuminary v2."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from .errors import ErrorCode, HackLuminaryError

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


class CodebaseAnalyzer:
    """Analyze repository source characteristics without network usage."""

    CODE_LANGUAGE_EXTENSIONS = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".jsx": "React",
        ".tsx": "React/TypeScript",
        ".java": "Java",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".php": "PHP",
        ".cs": "C#",
        ".cpp": "C++",
        ".c": "C",
        ".h": "C/C++",
        ".hpp": "C++",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".lua": "Lua",
        ".dart": "Dart",
        ".sh": "Shell",
        ".bash": "Bash",
        ".ps1": "PowerShell",
        ".sql": "SQL",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".vue": "Vue",
    }

    DOC_EXTENSIONS = {".md", ".rst", ".txt"}
    CONFIG_EXTENSIONS = {
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
        ".env",
        ".properties",
    }

    BINARY_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".ico",
        ".svg",
        ".pdf",
        ".zip",
        ".tar",
        ".gz",
        ".7z",
        ".mp3",
        ".mp4",
        ".mov",
        ".avi",
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".class",
        ".jar",
        ".pyc",
    }

    IGNORE_DIRS = {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        "vendor",
        "dist",
        "build",
        "target",
        "bin",
        "obj",
        "venv",
        ".venv",
        "env",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        "coverage",
        ".idea",
        ".vscode",
    }

    KEY_FILE_NAMES = {
        "main.py",
        "app.py",
        "server.py",
        "index.js",
        "main.js",
        "app.js",
        "main.ts",
        "index.ts",
        "main.go",
        "main.rs",
        "main.java",
    }

    FEATURE_PATTERNS = {
        "Authentication": ["auth", "login", "signup", "oauth", "jwt"],
        "Database": ["database", "postgres", "mysql", "mongo", "sqlite", "redis"],
        "API": ["api", "rest", "graphql", "fastapi", "express", "flask"],
        "AI": ["llm", "transformer", "embedding", "prompt", "inference"],
        "Realtime": ["websocket", "socket.io", "realtime"],
        "Payments": ["stripe", "paypal", "billing", "checkout"],
    }

    FRAMEWORK_HINTS = {
        "react": "React",
        "next": "Next.js",
        "nextjs": "Next.js",
        "vue": "Vue",
        "angular": "Angular",
        "express": "Express",
        "nestjs": "NestJS",
        "flask": "Flask",
        "django": "Django",
        "fastapi": "FastAPI",
        "spring": "Spring",
        "gin": "Gin",
        "actix": "Actix",
        "rocket": "Rocket",
    }

    def __init__(self, project_path: Path | str, max_bytes: int = 1_000_000):
        self.project_path = Path(project_path).resolve()
        self.max_bytes = max_bytes
        self.warnings: list[str] = []

        self.languages: Counter[str] = Counter()
        self.file_count = 0
        self.total_lines = 0
        self.key_files: list[str] = []
        self.dependencies: list[str] = []
        self.frameworks: list[str] = []
        self.features: list[str] = []
        self.docs_count = 0
        self.config_count = 0

    def analyze(self) -> dict:
        if not self.project_path.exists() or not self.project_path.is_dir():
            raise HackLuminaryError(
                ErrorCode.INVALID_INPUT,
                f"Project directory does not exist: {self.project_path}",
            )

        for file_path in self._iter_files(self.project_path):
            self._analyze_file(file_path)

        self._detect_dependencies()
        self._detect_frameworks()
        self._detect_features()

        return {
            "project_name": self.project_path.name,
            "languages": dict(sorted(self.languages.items(), key=lambda kv: (-kv[1], kv[0]))),
            "primary_language": self._primary_language(),
            "file_count": self.file_count,
            "total_lines": self.total_lines,
            "key_files": sorted(self.key_files),
            "dependencies": self.dependencies,
            "frameworks": self.frameworks,
            "features": self.features,
            "docs_count": self.docs_count,
            "config_count": self.config_count,
            "warnings": self.warnings,
        }

    def _iter_files(self, root: Path):
        stack = [root]
        while stack:
            directory = stack.pop()
            try:
                entries = sorted(directory.iterdir(), key=lambda p: p.name.lower())
            except PermissionError:
                self.warnings.append(f"Permission denied: {directory}")
                continue

            dirs: list[Path] = []
            files: list[Path] = []

            for entry in entries:
                if entry.is_symlink():
                    continue
                if entry.is_dir():
                    if self._should_ignore_dir(entry.name):
                        continue
                    dirs.append(entry)
                elif entry.is_file():
                    files.append(entry)

            for file_path in files:
                yield file_path

            for child in reversed(dirs):
                stack.append(child)

    @classmethod
    def _should_ignore_dir(cls, name: str) -> bool:
        lowered = name.lower()
        if lowered in cls.IGNORE_DIRS:
            return True
        # Ignore local virtualenv variants like `.venv-codex` or `venv311`.
        if lowered.startswith(".venv") or lowered.startswith("venv"):
            return True
        return False

    def _analyze_file(self, file_path: Path) -> None:
        ext = file_path.suffix.lower()

        if ext in self.BINARY_EXTENSIONS:
            return

        text = self._safe_read_text(file_path)
        if text is None:
            return

        line_count = len(text.splitlines())

        if ext in self.CODE_LANGUAGE_EXTENSIONS:
            language = self.CODE_LANGUAGE_EXTENSIONS[ext]
            self.languages[language] += 1
            self.file_count += 1
            self.total_lines += line_count

            if file_path.name in self.KEY_FILE_NAMES:
                self.key_files.append(str(file_path.relative_to(self.project_path)))
        elif ext in self.DOC_EXTENSIONS:
            self.docs_count += 1
        elif ext in self.CONFIG_EXTENSIONS:
            self.config_count += 1

    def _safe_read_text(self, file_path: Path) -> str | None:
        try:
            with file_path.open("rb") as handle:
                raw = handle.read(self.max_bytes + 1)
        except (PermissionError, OSError):
            self.warnings.append(f"Could not read file: {file_path}")
            return None

        if len(raw) > self.max_bytes:
            self.warnings.append(f"Skipped large file: {file_path}")
            return None

        if b"\x00" in raw:
            return None

        return raw.decode("utf-8", errors="ignore")

    def _primary_language(self) -> str:
        if not self.languages:
            return "Unknown"
        return max(self.languages.items(), key=lambda item: item[1])[0]

    def _detect_dependencies(self) -> None:
        parsers = {
            "package.json": self._parse_package_json,
            "requirements.txt": self._parse_requirements,
            "pyproject.toml": self._parse_pyproject,
            "go.mod": self._parse_go_mod,
            "Cargo.toml": self._parse_cargo_toml,
        }

        deps: list[str] = []
        for filename, parser in parsers.items():
            path = self.project_path / filename
            if path.exists():
                deps.extend(parser(path))

        seen = set()
        ordered: list[str] = []
        for dep in deps:
            key = dep.lower()
            if key in seen:
                continue
            seen.add(key)
            ordered.append(dep)

        self.dependencies = ordered[:25]

    def _parse_package_json(self, path: Path) -> list[str]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []

        deps = []
        for section in ("dependencies", "devDependencies"):
            if isinstance(data.get(section), dict):
                deps.extend(data[section].keys())
        return list(sorted(set(deps), key=str.lower))

    def _parse_requirements(self, path: Path) -> list[str]:
        deps: list[str] = []
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            cleaned = line.strip()
            if not cleaned or cleaned.startswith("#"):
                continue
            name = re.split(r"[<>=~! ]", cleaned, maxsplit=1)[0]
            if name:
                deps.append(name)
        return deps

    def _parse_pyproject(self, path: Path) -> list[str]:
        try:
            with path.open("rb") as handle:
                data = tomllib.load(handle)
        except Exception:
            return []

        deps: list[str] = []
        project = data.get("project", {})
        for dep in project.get("dependencies", []) or []:
            name = re.split(r"[<>=~! ]", str(dep), maxsplit=1)[0]
            if name:
                deps.append(name)

        poetry = data.get("tool", {}).get("poetry", {})
        if isinstance(poetry.get("dependencies"), dict):
            for dep_name in poetry["dependencies"].keys():
                if dep_name != "python":
                    deps.append(dep_name)

        return deps

    def _parse_go_mod(self, path: Path) -> list[str]:
        deps: list[str] = []
        in_require_block = False

        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if stripped.startswith("require ("):
                in_require_block = True
                continue
            if in_require_block and stripped == ")":
                in_require_block = False
                continue

            if stripped.startswith("require "):
                parts = stripped.split()
                if len(parts) >= 2:
                    deps.append(parts[1])
                continue

            if in_require_block and stripped:
                parts = stripped.split()
                if parts:
                    deps.append(parts[0])

        return deps

    def _parse_cargo_toml(self, path: Path) -> list[str]:
        deps: list[str] = []
        in_deps = False

        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if stripped.startswith("[dependencies"):
                in_deps = True
                continue
            if in_deps and stripped.startswith("["):
                in_deps = False
                continue
            if in_deps and "=" in stripped:
                name = stripped.split("=", maxsplit=1)[0].strip()
                if name:
                    deps.append(name)

        return deps

    def _detect_frameworks(self) -> None:
        detected: list[str] = []
        dep_text = " ".join(self.dependencies).lower()

        for hint, framework in sorted(self.FRAMEWORK_HINTS.items(), key=lambda kv: kv[1]):
            if hint in dep_text and framework not in detected:
                detected.append(framework)

        self.frameworks = detected

    def _detect_features(self) -> None:
        corpus = []

        readme = self.project_path / "README.md"
        if readme.exists():
            corpus.append(readme.read_text(encoding="utf-8", errors="ignore").lower())

        for relative_path in self.key_files[:5]:
            path = self.project_path / relative_path
            if path.exists():
                text = self._safe_read_text(path)
                if text:
                    corpus.append(text.lower())

        content = "\n".join(corpus)

        features: list[str] = []
        for feature, patterns in self.FEATURE_PATTERNS.items():
            if any(pattern in content for pattern in patterns):
                features.append(feature)

        self.features = features
