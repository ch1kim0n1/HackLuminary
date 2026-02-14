"""End-to-end generation and validation pipeline."""

from __future__ import annotations

from pathlib import Path

from .ai_pipeline import enhance_slides_with_ai
from .analyzer import CodebaseAnalyzer
from .config import load_resolved_config
from .document_parser import DocumentParser
from .errors import ErrorCode, HackLuminaryError
from .evidence import build_evidence, evidence_index
from .git_context import collect_git_context
from .presentation_generator import PresentationGenerator
from .slides import build_deterministic_slides, resolve_slide_types


def run_generation(
    project_dir: str | Path,
    additional_docs: list[str] | None = None,
    requested_slide_types: list[str] | None = None,
    max_slides: int | None = None,
    cli_overrides: dict | None = None,
) -> dict:
    """Generate slide payload and rendered outputs using resolved config."""

    project_path = Path(project_dir).resolve()
    if not project_path.exists() or not project_path.is_dir():
        raise HackLuminaryError(
            ErrorCode.INVALID_INPUT,
            f"Project directory does not exist: {project_path}",
        )

    config = load_resolved_config(project_path, cli_overrides=cli_overrides)

    analyzer = CodebaseAnalyzer(project_path)
    code_analysis = analyzer.analyze()

    parser = DocumentParser(project_path, additional_docs=additional_docs)
    doc_data = parser.parse()

    git_cfg = config["git"]
    git_context = collect_git_context(
        project_path,
        include_branch_context=bool(git_cfg.get("include_branch_context", True)),
        base_branch=git_cfg.get("base_branch"),
    )

    evidence = build_evidence(code_analysis, doc_data, git_context, project_path=project_path)
    evidence_map = evidence_index(evidence)

    resolved_max_slides = max_slides if max_slides is not None else config["general"].get("max_slides")
    slide_types = resolve_slide_types(
        requested=requested_slide_types,
        max_slides=resolved_max_slides,
        has_git_context=bool(git_context.get("available") and git_context.get("base_branch")),
    )

    deterministic = build_deterministic_slides(
        code_analysis=code_analysis,
        doc_data=doc_data,
        git_context=git_context,
        evidence_ids=set(evidence_map.keys()),
        slide_types=slide_types,
    )

    slides, quality_report = enhance_slides_with_ai(deterministic, evidence, config)

    metadata = {
        "project": doc_data.get("title") or code_analysis.get("project_name", ""),
        "languages": code_analysis.get("languages", {}),
        "dependencies": code_analysis.get("dependencies", []),
        "frameworks": code_analysis.get("frameworks", []),
        "file_count": code_analysis.get("file_count", 0),
        "total_lines": code_analysis.get("total_lines", 0),
        "docs_count": code_analysis.get("docs_count", 0),
        "config_count": code_analysis.get("config_count", 0),
    }

    payload = {
        "schema_version": "2.1",
        "metadata": metadata,
        "git_context": {
            "branch": git_context.get("branch", ""),
            "base_branch": git_context.get("base_branch", ""),
            "head_sha": git_context.get("head_sha", ""),
            "base_sha": git_context.get("base_sha", ""),
            "changed_files_count": git_context.get("changed_files_count", 0),
            "top_changed_paths": git_context.get("top_changed_paths", []),
            "change_summary": git_context.get("change_summary", ""),
        },
        "slides": slides,
        "evidence": evidence,
        "quality_report": quality_report,
    }

    renderer = PresentationGenerator(
        slides=slides,
        metadata=metadata,
        theme=config["general"].get("theme", "default"),
    )

    fmt = config["general"].get("format", "both")
    html_output = renderer.generate_html() if fmt in {"html", "both"} else None
    markdown_output = renderer.generate_markdown() if fmt in {"markdown", "both"} else None

    warnings = []
    warnings.extend(analyzer.warnings)
    warnings.extend(parser.warnings)
    warnings.extend(git_context.get("warnings", []))

    return {
        "config": config,
        "payload": payload,
        "html": html_output,
        "markdown": markdown_output,
        "warnings": warnings,
    }


def run_validation(
    project_dir: str | Path,
    additional_docs: list[str] | None = None,
    requested_slide_types: list[str] | None = None,
    max_slides: int | None = None,
    cli_overrides: dict | None = None,
) -> dict:
    """Validate end-to-end generation inputs and quality without writing files."""

    result = run_generation(
        project_dir=project_dir,
        additional_docs=additional_docs,
        requested_slide_types=requested_slide_types,
        max_slides=max_slides,
        cli_overrides=cli_overrides,
    )

    payload = result["payload"]
    report = payload["quality_report"]

    return {
        "status": report.get("status", "fail"),
        "errors": report.get("errors", []),
        "warnings": result.get("warnings", []) + report.get("warnings", []),
        "metrics": report.get("metrics", {}),
        "slide_count": len(payload.get("slides", [])),
        "evidence_count": len(payload.get("evidence", [])),
        "git_context": payload.get("git_context", {}),
    }
