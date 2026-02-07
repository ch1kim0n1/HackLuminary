"""Tests for the codebase analyzer."""
import tempfile
import pytest
from pathlib import Path
from hackluminary.analyzer import CodebaseAnalyzer


def test_analyzer_detects_python_files():
    """Test that analyzer correctly detects Python files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        py_file = Path(tmpdir) / "test.py"
        py_file.write_text("print('hello')\nprint('world')\n")
        
        analyzer = CodebaseAnalyzer(tmpdir)
        result = analyzer.analyze()
        
        assert result is not None
        assert result['primary_language'] == 'Python'
        assert result['file_count'] == 1
        assert result['total_lines'] == 2


def test_analyzer_detects_javascript_files():
    """Test that analyzer correctly detects JavaScript files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        js_file = Path(tmpdir) / "app.js"
        js_file.write_text("console.log('hello');\nconsole.log('world');\n")
        
        analyzer = CodebaseAnalyzer(tmpdir)
        result = analyzer.analyze()
        
        assert result is not None
        assert result['primary_language'] == 'JavaScript'
        assert result['file_count'] == 1


def test_analyzer_detects_multiple_languages():
    """Test that analyzer correctly detects multiple languages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        (Path(tmpdir) / "test.py").write_text("print('hello')\n")
        (Path(tmpdir) / "app.js").write_text("console.log('hello');\n")
        (Path(tmpdir) / "style.css").write_text("body { margin: 0; }\n")
        
        analyzer = CodebaseAnalyzer(tmpdir)
        result = analyzer.analyze()
        
        assert result is not None
        assert result['file_count'] == 3
        assert len(result['languages']) == 3


def test_analyzer_ignores_common_directories():
    """Test that analyzer ignores node_modules, .git, etc."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create ignored directory
        node_modules = Path(tmpdir) / "node_modules"
        node_modules.mkdir()
        (node_modules / "lib.js").write_text("console.log('ignored');\n")
        
        # Create regular file
        (Path(tmpdir) / "app.js").write_text("console.log('counted');\n")
        
        analyzer = CodebaseAnalyzer(tmpdir)
        result = analyzer.analyze()
        
        assert result is not None
        assert result['file_count'] == 1


def test_analyzer_detects_package_json_dependencies():
    """Test that analyzer detects dependencies from package.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = Path(tmpdir) / "package.json"
        package_json.write_text('{"dependencies": {"react": "^18.0.0", "express": "^4.18.0"}}')
        
        # Add a code file so analyzer doesn't return None
        (Path(tmpdir) / "app.js").write_text("console.log('test');\n")
        
        analyzer = CodebaseAnalyzer(tmpdir)
        result = analyzer.analyze()
        
        assert result is not None
        assert 'react' in result['dependencies']
        assert 'express' in result['dependencies']


def test_analyzer_detects_requirements_txt():
    """Test that analyzer detects dependencies from requirements.txt."""
    with tempfile.TemporaryDirectory() as tmpdir:
        requirements = Path(tmpdir) / "requirements.txt"
        requirements.write_text("flask>=2.0.0\nrequests>=2.28.0\n")
        
        # Add a code file so analyzer doesn't return None
        (Path(tmpdir) / "app.py").write_text("print('test')\n")
        
        analyzer = CodebaseAnalyzer(tmpdir)
        result = analyzer.analyze()
        
        assert result is not None
        assert 'flask' in result['dependencies']
        assert 'requests' in result['dependencies']


def test_analyzer_returns_result_for_empty_directory():
    """Test that analyzer returns result even for empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analyzer = CodebaseAnalyzer(tmpdir)
        result = analyzer.analyze()
        
        assert result is not None
        assert result['file_count'] == 0
        assert result['primary_language'] == 'Unknown'
        assert result['project_name'] == Path(tmpdir).name


def test_analyzer_tracks_key_files():
    """Test that analyzer tracks key files like main.py."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "main.py").write_text("print('main')\n")
        (Path(tmpdir) / "utils.py").write_text("print('utils')\n")
        
        analyzer = CodebaseAnalyzer(tmpdir)
        result = analyzer.analyze()
        
        assert result is not None
        assert 'main.py' in result['key_files']
        assert 'utils.py' not in result['key_files']
