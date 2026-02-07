"""CLI interface for HackLuminary."""
import click
import sys
import os
from pathlib import Path
from .analyzer import CodebaseAnalyzer
from .document_parser import DocumentParser
from .presentation_generator import PresentationGenerator


@click.command()
@click.option('--project-dir', type=click.Path(exists=True, file_okay=False, dir_okay=True),
              required=True, help='Path to the project directory to analyze')
@click.option('--output', type=click.Path(), default='presentation.html',
              help='Output file path (default: presentation.html)')
@click.option('--docs', type=click.Path(exists=True), multiple=True,
              help='Additional documentation files to include')
def main(project_dir, output, docs):
    """Generate a hackathon presentation from a codebase.
    
    This tool analyzes your project's codebase and documentation to create
    a complete hackathon-ready presentation following standard judging flow:
    Problem -> Solution -> Demo -> Impact -> Tech -> Future.
    """
    try:
        click.echo(f"🚀 HackLuminary - Generating presentation for {project_dir}")
        
        # Validate inputs
        project_path = Path(project_dir).resolve()
        if not project_path.exists():
            click.echo(f"❌ Error: Project directory does not exist: {project_dir}", err=True)
            sys.exit(1)
        
        # Analyze codebase
        click.echo("📊 Analyzing codebase...")
        analyzer = CodebaseAnalyzer(project_path)
        code_analysis = analyzer.analyze()
        
        # Parse documentation
        click.echo("📄 Parsing documentation...")
        doc_parser = DocumentParser(project_path, list(docs))
        doc_data = doc_parser.parse()
        
        # Generate presentation
        click.echo("🎨 Generating presentation...")
        generator = PresentationGenerator(code_analysis, doc_data)
        html_output = generator.generate()
        
        # Write output
        output_path = Path(output).resolve()
        output_path.write_text(html_output, encoding='utf-8')
        
        click.echo(f"✅ Presentation generated successfully: {output_path}")
        click.echo(f"📂 Open {output_path} in your browser to view")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
