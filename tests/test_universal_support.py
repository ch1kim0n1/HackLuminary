"""Additional tests for universal project support."""
import tempfile
import pytest
from pathlib import Path
from hackluminary.analyzer import CodebaseAnalyzer
from hackluminary.presentation_generator import PresentationGenerator


def test_analyzer_handles_unknown_languages():
    """Test that analyzer handles unknown file extensions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files with unknown extensions
        (Path(tmpdir) / 'app.xyz').write_text('some code\nmore code\n')
        (Path(tmpdir) / 'config.abc').write_text('config = true\n')
        
        analyzer = CodebaseAnalyzer(tmpdir)
        result = analyzer.analyze()
        
        # Should still return a result
        assert result is not None
        assert result['project_name'] == Path(tmpdir).name


def test_analyzer_detects_haskell():
    """Test that analyzer detects Haskell files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / 'Main.hs').write_text('main = putStrLn "Hello"\n')
        
        analyzer = CodebaseAnalyzer(tmpdir)
        result = analyzer.analyze()
        
        assert result is not None
        assert result['primary_language'] == 'Haskell'
        assert result['file_count'] == 1


def test_analyzer_detects_shell_scripts():
    """Test that analyzer detects shell scripts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / 'deploy.sh').write_text('#!/bin/bash\necho "deploying"\n')
        (Path(tmpdir) / 'setup.bash').write_text('#!/bin/bash\necho "setup"\n')
        
        analyzer = CodebaseAnalyzer(tmpdir)
        result = analyzer.analyze()
        
        assert result is not None
        assert 'Shell' in result['languages'] or 'Bash' in result['languages']
        assert result['file_count'] == 2


def test_analyzer_handles_mixed_known_unknown():
    """Test analyzer with mix of known and unknown files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / 'app.py').write_text('print("hello")\nprint("world")\n')
        (Path(tmpdir) / 'utils.py').write_text('def helper(): pass\n')
        (Path(tmpdir) / 'weird.xyz').write_text('some content\n')
        (Path(tmpdir) / 'config.toml').write_text('[config]\n')
        
        analyzer = CodebaseAnalyzer(tmpdir)
        result = analyzer.analyze()
        
        assert result is not None
        assert result['primary_language'] == 'Python'
        # Should count Python and TOML files
        assert result['file_count'] >= 2
        assert 'Python' in result['languages']
        assert 'TOML' in result['languages']


def test_analyzer_skips_binary_files():
    """Test that analyzer skips binary files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / 'app.py').write_text('print("hello")\n')
        (Path(tmpdir) / 'binary.exe').write_bytes(b'\x00\x01\x02\x03')
        (Path(tmpdir) / 'image.png').write_bytes(b'\x89PNG\r\n\x1a\n')
        
        analyzer = CodebaseAnalyzer(tmpdir)
        result = analyzer.analyze()
        
        assert result is not None
        # Should only count Python file, not binary files
        assert result['file_count'] == 1


def test_generator_handles_empty_codebase():
    """Test presentation generation with no code files."""
    code_analysis = {
        'languages': {},
        'primary_language': 'Unknown',
        'file_count': 0,
        'total_lines': 0,
        'key_files': [],
        'dependencies': [],
        'frameworks': [],
        'project_name': 'EmptyProject',
    }
    
    doc_data = {
        'title': 'Empty Project',
        'description': 'A project with no code yet',
        'problem': '',
        'solution': '',
        'features': [],
        'installation': '',
        'usage': '',
    }
    
    generator = PresentationGenerator(code_analysis, doc_data)
    html = generator.generate()
    
    # Should generate valid HTML
    assert '<html' in html
    assert 'Empty Project' in html
    # Should handle unknown language gracefully
    assert 'Unknown' not in html or 'innovative' in html.lower()


def test_generator_handles_unknown_language():
    """Test presentation generation with unknown language."""
    code_analysis = {
        'languages': {'Other': 5},
        'primary_language': 'Unknown',
        'file_count': 5,
        'total_lines': 100,
        'key_files': [],
        'dependencies': [],
        'frameworks': [],
        'project_name': 'MysteryProject',
    }
    
    doc_data = {
        'title': 'Mystery Project',
        'description': 'A unique project',
        'problem': '',
        'solution': '',
        'features': [],
        'installation': '',
        'usage': '',
    }
    
    generator = PresentationGenerator(code_analysis, doc_data)
    html = generator.generate()
    
    # Should generate valid HTML with generic content
    assert '<html' in html
    assert 'Mystery Project' in html
    assert '5 files' in html
    assert '100 lines' in html


def test_analyzer_detects_yaml_files():
    """Test that analyzer detects YAML configuration files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / 'config.yaml').write_text('key: value\n')
        (Path(tmpdir) / 'docker-compose.yml').write_text('version: "3"\n')
        
        analyzer = CodebaseAnalyzer(tmpdir)
        result = analyzer.analyze()
        
        assert result is not None
        assert 'YAML' in result['languages']
        assert result['file_count'] == 2


def test_generator_shows_multiple_languages():
    """Test that generator shows multiple languages in tech stack."""
    code_analysis = {
        'languages': {'Python': 10, 'JavaScript': 8, 'HTML': 5, 'CSS': 3},
        'primary_language': 'Python',
        'file_count': 26,
        'total_lines': 1500,
        'key_files': [],
        'dependencies': [],
        'frameworks': [],
        'project_name': 'FullStackProject',
    }
    
    doc_data = {
        'title': 'Full Stack Project',
        'description': 'A complete web application',
        'problem': '',
        'solution': '',
        'features': [],
        'installation': '',
        'usage': '',
    }
    
    generator = PresentationGenerator(code_analysis, doc_data)
    html = generator.generate()
    
    # Should show multiple languages
    assert 'Python' in html
    assert 'JavaScript' in html
    # Should show the languages list
    assert '**Languages:**' in html or 'Languages' in html
