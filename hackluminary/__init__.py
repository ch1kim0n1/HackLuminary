"""HackLuminary - CLI tool for generating hackathon presentations."""
__version__ = "1.0.0"

from pathlib import Path
from .analyzer import CodebaseAnalyzer
from .document_parser import DocumentParser
from .presentation_generator import PresentationGenerator


def generate_presentation(project_dir, output=None, fmt="both", docs=None,
                          theme_config=None):
    """Generate a hackathon presentation from a codebase.

    Args:
        project_dir: Path to the project directory to analyze.
        output: Output file path (default: 'presentation.html' in cwd).
        fmt: Output format - 'html', 'markdown', 'both', or 'json'.
        docs: List of additional documentation file paths.
        theme_config: Dict with theme overrides (background, text, gradients).

    Returns:
        dict with keys: html, markdown, slides, metadata.
              html/markdown are None if not requested by fmt.
    """
    project_path = Path(project_dir).resolve()
    if not project_path.is_dir():
        raise ValueError(f"Project directory does not exist: {project_path}")

    analyzer = CodebaseAnalyzer(project_path)
    code_analysis = analyzer.analyze()

    doc_parser = DocumentParser(project_path, list(docs or []))
    doc_data = doc_parser.parse()

    generator = PresentationGenerator(code_analysis, doc_data,
                                      theme_config=theme_config)

    result = {
        "html": None,
        "markdown": None,
        "slides": generator.get_slides_data(),
        "metadata": {
            "project": doc_data.get("title", ""),
            "languages": code_analysis.get("languages", {}),
            "dependencies": code_analysis.get("dependencies", []),
            "frameworks": code_analysis.get("frameworks", []),
            "file_count": code_analysis.get("file_count", 0),
            "total_lines": code_analysis.get("total_lines", 0),
        },
    }

    if fmt in ("html", "both"):
        result["html"] = generator.generate()
    if fmt in ("markdown", "both"):
        result["markdown"] = generator.generate_markdown()

    # Write files if output path specified
    if output and fmt != "json":
        output_path = Path(output).resolve()
        if result["html"]:
            html_path = output_path if fmt == "html" else output_path.with_suffix(".html")
            html_path.write_text(result["html"], encoding="utf-8")
        if result["markdown"]:
            md_path = output_path.with_suffix(".md") if fmt == "both" else output_path
            md_path.write_text(result["markdown"], encoding="utf-8")

    return result
