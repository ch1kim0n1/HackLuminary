"""Tests for the document parser."""
import tempfile
import pytest
from pathlib import Path
from hackluminary.document_parser import DocumentParser


def test_parser_finds_readme():
    """Test that parser finds README.md."""
    with tempfile.TemporaryDirectory() as tmpdir:
        readme = Path(tmpdir) / "README.md"
        readme.write_text("# Test Project\n\nThis is a test project.")
        
        parser = DocumentParser(tmpdir)
        result = parser.parse()
        
        assert result['title'] == 'Test Project'
        assert 'test project' in result['description'].lower()


def test_parser_extracts_title():
    """Test that parser extracts title from README."""
    with tempfile.TemporaryDirectory() as tmpdir:
        readme = Path(tmpdir) / "README.md"
        readme.write_text("# My Awesome Project\n\nDescription here.")
        
        parser = DocumentParser(tmpdir)
        result = parser.parse()
        
        assert result['title'] == 'My Awesome Project'


def test_parser_extracts_problem_section():
    """Test that parser extracts problem section."""
    with tempfile.TemporaryDirectory() as tmpdir:
        readme = Path(tmpdir) / "README.md"
        readme.write_text("""# Project
        
## Problem
The current systems are inefficient.

## Solution
Our solution fixes this.
""")
        
        parser = DocumentParser(tmpdir)
        result = parser.parse()
        
        assert 'inefficient' in result['problem'].lower()


def test_parser_extracts_solution_section():
    """Test that parser extracts solution section."""
    with tempfile.TemporaryDirectory() as tmpdir:
        readme = Path(tmpdir) / "README.md"
        readme.write_text("""# Project
        
## Solution
We use advanced algorithms to solve the problem.
""")
        
        parser = DocumentParser(tmpdir)
        result = parser.parse()
        
        assert 'algorithms' in result['solution'].lower()


def test_parser_extracts_features():
    """Test that parser extracts features from bullet points."""
    with tempfile.TemporaryDirectory() as tmpdir:
        readme = Path(tmpdir) / "README.md"
        readme.write_text("""# Project
        
## Features
* Fast performance
* Easy to use
* Secure by default
""")
        
        parser = DocumentParser(tmpdir)
        result = parser.parse()
        
        assert len(result['features']) == 3
        assert 'Fast performance' in result['features']
        assert 'Easy to use' in result['features']


def test_parser_handles_missing_readme():
    """Test that parser handles missing README gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        parser = DocumentParser(tmpdir)
        result = parser.parse()
        
        # Should use directory name as title
        assert result['title'] is not None
        assert result['description'] == ''


def test_parser_handles_additional_docs():
    """Test that parser handles additional documentation files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        doc = Path(tmpdir) / "OVERVIEW.md"
        doc.write_text("Additional documentation content.")
        
        parser = DocumentParser(tmpdir, [str(doc)])
        result = parser.parse()
        
        assert 'Additional' in result['description']


def test_parser_extracts_installation_instructions():
    """Test that parser extracts installation section."""
    with tempfile.TemporaryDirectory() as tmpdir:
        readme = Path(tmpdir) / "README.md"
        readme.write_text("""# Project
        
## Installation
Run `npm install` to install dependencies.
""")
        
        parser = DocumentParser(tmpdir)
        result = parser.parse()
        
        assert 'npm install' in result['installation']


def test_parser_case_insensitive_section_matching():
    """Test that parser matches section headers case-insensitively."""
    with tempfile.TemporaryDirectory() as tmpdir:
        readme = Path(tmpdir) / "README.md"
        readme.write_text("""# Project
        
## PROBLEM
This is the problem.

## SOLUTION  
This is the solution.
""")
        
        parser = DocumentParser(tmpdir)
        result = parser.parse()
        
        assert result['problem'] != ''
        assert result['solution'] != ''
