"""Renderer tests for HTML sanitization and offline guarantees."""

from hackluminary.presentation_generator import PresentationGenerator


def _sample_slides():
    return [
        {
            "id": "title",
            "type": "title",
            "title": "Demo",
            "subtitle": "<script>alert('x')</script>",
            "evidence_refs": ["doc.title"],
            "claims": [{"text": "Demo claim", "evidence_refs": ["doc.title"], "confidence": 0.9}],
            "notes": "Talk track here.",
        },
        {
            "id": "tech",
            "type": "list",
            "title": "Technology Stack",
            "list_items": ["Python", "FastAPI"],
            "evidence_refs": ["repo.languages"],
            "claims": [{"text": "Uses Python", "evidence_refs": ["repo.languages"], "confidence": 0.91}],
            "visuals": [
                {
                    "id": "media.demo",
                    "type": "image",
                    "source_path": "assets/demo.png",
                    "alt": "Demo screenshot",
                    "caption": "Demo UI",
                    "confidence": 0.9,
                }
            ],
        },
        {
            "id": "delta",
            "type": "list",
            "title": "Branch Delta",
            "list_items": ["2 files changed"],
            "evidence_refs": ["git.change_summary"],
            "claims": [{"text": "Changed 2 files", "evidence_refs": ["git.change_summary"], "confidence": 0.95}],
        },
    ]


def test_html_is_sanitized_and_offline():
    generator = PresentationGenerator(_sample_slides(), metadata={"project": "Demo"}, theme="default")
    html = generator.generate_html()

    assert "<script>alert('x')</script>" not in html
    assert "&lt;script&gt;alert" in html
    assert "http://" not in html
    assert "https://" not in html
    assert "claim-chip" in html
    assert "presenter-hud" in html
    assert "speaker-notes" in html
    assert "image-modal" in html


def test_markdown_supports_tech_and_delta_sections():
    generator = PresentationGenerator(_sample_slides(), metadata={"project": "Demo"}, theme="default")
    md = generator.generate_markdown()

    assert "## Technology Stack" in md
    assert "## Branch Delta" in md
    assert "- Python" in md


def test_themes_change_rendered_css_variables():
    slides = _sample_slides()
    default_html = PresentationGenerator(slides, metadata={"project": "Demo"}, theme="default").generate_html()
    dark_html = PresentationGenerator(slides, metadata={"project": "Demo"}, theme="dark").generate_html()

    assert default_html != dark_html
