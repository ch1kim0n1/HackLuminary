"""CLI interface for HackLuminary."""
import click
import sys
import json
import webbrowser
from pathlib import Path
from .analyzer import CodebaseAnalyzer
from .document_parser import DocumentParser
from .presentation_generator import PresentationGenerator


@click.command()
@click.option('--project-dir', type=click.Path(exists=True, file_okay=False, dir_okay=True),
              required=True, help='Path to the project directory to analyze')
@click.option('--output', type=click.Path(), default='presentation.html',
              help='Output file path (default: presentation.html)')
@click.option('--format', 'fmt', type=click.Choice(['html', 'markdown', 'both', 'json']),
              default='both',
              help='Output format: html, markdown, both, or json (default: both)')
@click.option('--docs', type=click.Path(exists=True), multiple=True,
              help='Additional documentation files to include')
@click.option('--theme', type=click.Choice(['default', 'dark', 'minimal', 'colorful']),
              default='default', help='Presentation visual theme (default: default)')
@click.option('--theme-file', type=click.Path(exists=True), default=None,
              help='Custom theme JSON file (overrides --theme)')
@click.option('--html-template', type=click.Path(exists=True), default=None,
              help='Custom Jinja2 HTML template file')
@click.option('--open', 'auto_open', is_flag=True, default=False,
              help='Auto-open the HTML presentation in browser')
@click.option('--slides', default=None,
              help='Comma-separated slide types to include (title,problem,solution,demo,impact,tech,future,closing)')
@click.option('--max-slides', type=int, default=None,
              help='Maximum number of slides (auto-selects most important)')
def main(project_dir, output, fmt, docs, theme, theme_file, html_template, auto_open, slides, max_slides):
    """Generate a hackathon presentation from a codebase.

    This tool analyzes your project's codebase and documentation to create
    a complete hackathon-ready presentation following standard judging flow:
    Problem -> Solution -> Demo -> Impact -> Tech -> Future.
    """
    try:
        is_json = fmt == 'json'
        if not is_json:
            click.echo(f"HackLuminary - Generating presentation for {project_dir}")

        # Validate inputs
        project_path = Path(project_dir).resolve()

        # Load custom theme if provided
        theme_config = None
        if theme_file:
            theme_config = json.loads(Path(theme_file).read_text(encoding='utf-8'))
        elif theme != 'default':
            theme_config = _get_builtin_theme(theme)

        # Analyze codebase
        if not is_json:
            click.echo("Analyzing codebase...")
        analyzer = CodebaseAnalyzer(project_path)
        code_analysis = analyzer.analyze()

        # Parse documentation
        if not is_json:
            click.echo("Parsing documentation...")
        doc_parser = DocumentParser(project_path, list(docs))
        doc_data = doc_parser.parse()

        # Parse slide selection
        slide_types = None
        if slides:
            slide_types = [s.strip() for s in slides.split(',')]

        # Generate presentation
        if not is_json:
            click.echo("Generating presentation...")
        generator = PresentationGenerator(
            code_analysis, doc_data,
            theme_config=theme_config,
            slide_types=slide_types,
            max_slides=max_slides,
            html_template_path=html_template,
        )

        # JSON output mode
        if is_json:
            result = {
                "slides": generator.get_slides_data(),
                "metadata": {
                    "project": doc_data.get('title', ''),
                    "languages": code_analysis.get('languages', {}),
                    "dependencies": code_analysis.get('dependencies', []),
                    "frameworks": code_analysis.get('frameworks', []),
                    "file_count": code_analysis.get('file_count', 0),
                    "total_lines": code_analysis.get('total_lines', 0),
                }
            }
            click.echo(json.dumps(result, indent=2))
            return

        # Write output based on format
        output_path = Path(output).resolve()
        html_path = None

        if fmt in ['html', 'both']:
            html_output = generator.generate()
            html_path = output_path if fmt == 'html' else output_path.with_suffix('.html')
            html_path.write_text(html_output, encoding='utf-8')
            click.echo(f"HTML presentation: {html_path}")

        if fmt in ['markdown', 'both']:
            markdown_output = generator.generate_markdown()
            md_path = output_path.with_suffix('.md') if fmt == 'both' else output_path
            md_path.write_text(markdown_output, encoding='utf-8')
            click.echo(f"Markdown presentation: {md_path}")

        click.echo("Presentation generated successfully!")

        if auto_open and html_path and html_path.exists():
            webbrowser.open(str(html_path))

        if fmt in ['markdown', 'both']:
            click.echo("Tip: Open the .md file in VS Code with Marp extension for live preview")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


def _get_builtin_theme(name):
    """Return a built-in theme configuration."""
    themes = {
        'dark': {
            'background': '#0f0f0f',
            'text': '#ffffff',
            'gradients': [
                'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
                'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
                'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
                'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',
                'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
            ],
        },
        'minimal': {
            'background': '#ffffff',
            'text': '#1a1a2e',
            'gradients': [
                'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
                'linear-gradient(135deg, #e2e8f0 0%, #edf2f7 100%)',
                'linear-gradient(135deg, #fafafa 0%, #e5e5e5 100%)',
                'linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%)',
                'linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%)',
                'linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%)',
                'linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%)',
                'linear-gradient(135deg, #fafafa 0%, #f0f0f0 100%)',
            ],
        },
        'colorful': {
            'background': '#0f0f0f',
            'text': '#ffffff',
            'gradients': [
                'linear-gradient(135deg, #ff6b6b 0%, #feca57 100%)',
                'linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%)',
                'linear-gradient(135deg, #fd79a8 0%, #e84393 100%)',
                'linear-gradient(135deg, #00cec9 0%, #0984e3 100%)',
                'linear-gradient(135deg, #55efc4 0%, #00b894 100%)',
                'linear-gradient(135deg, #fdcb6e 0%, #e17055 100%)',
                'linear-gradient(135deg, #74b9ff 0%, #0984e3 100%)',
                'linear-gradient(135deg, #dfe6e9 0%, #b2bec3 100%)',
            ],
        },
    }
    return themes.get(name)


if __name__ == '__main__':
    main()
