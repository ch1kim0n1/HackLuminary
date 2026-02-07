"""Tests for the presentation generator."""
import pytest
from hackluminary.presentation_generator import PresentationGenerator


def test_generator_creates_all_slides():
    """Test that generator creates all required slides."""
    code_analysis = {
        'languages': {'Python': 5},
        'primary_language': 'Python',
        'file_count': 10,
        'total_lines': 500,
        'key_files': ['main.py'],
        'dependencies': ['flask', 'requests'],
        'frameworks': ['Flask'],
        'project_name': 'TestProject',
    }
    
    doc_data = {
        'title': 'Test Project',
        'description': 'A test project',
        'problem': 'Test problem',
        'solution': 'Test solution',
        'features': ['Feature 1', 'Feature 2'],
        'installation': 'pip install',
        'usage': 'python main.py',
    }
    
    generator = PresentationGenerator(code_analysis, doc_data)
    html = generator.generate()
    
    # Check that HTML contains all key sections
    assert 'Test Project' in html
    assert 'The Problem' in html
    assert 'Our Solution' in html
    assert 'Key Features' in html
    assert 'Impact & Benefits' in html
    assert 'Technology Stack' in html
    assert 'Future Plans' in html
    assert 'Thank You' in html


def test_generator_includes_code_analysis_data():
    """Test that generator includes code analysis data."""
    code_analysis = {
        'languages': {'JavaScript': 15},
        'primary_language': 'JavaScript',
        'file_count': 20,
        'total_lines': 1000,
        'key_files': ['index.js'],
        'dependencies': ['react', 'express'],
        'frameworks': ['React', 'Express'],
        'project_name': 'JSProject',
    }
    
    doc_data = {
        'title': 'JS Project',
        'description': 'JavaScript project',
        'problem': '',
        'solution': '',
        'features': [],
        'installation': '',
        'usage': '',
    }
    
    generator = PresentationGenerator(code_analysis, doc_data)
    html = generator.generate()
    
    assert 'JavaScript' in html
    assert 'React' in html
    assert 'Express' in html
    assert '20 files' in html


def test_generator_handles_empty_features():
    """Test that generator handles empty features gracefully."""
    code_analysis = {
        'languages': {'Python': 5},
        'primary_language': 'Python',
        'file_count': 5,
        'total_lines': 200,
        'key_files': [],
        'dependencies': [],
        'frameworks': [],
        'project_name': 'MinimalProject',
    }
    
    doc_data = {
        'title': 'Minimal Project',
        'description': '',
        'problem': '',
        'solution': '',
        'features': [],
        'installation': '',
        'usage': '',
    }
    
    generator = PresentationGenerator(code_analysis, doc_data)
    html = generator.generate()
    
    # Should still generate valid HTML
    assert '<html' in html
    assert 'Minimal Project' in html
    assert 'Key Features' in html


def test_generator_creates_valid_html():
    """Test that generator creates valid HTML structure."""
    code_analysis = {
        'languages': {'Python': 1},
        'primary_language': 'Python',
        'file_count': 1,
        'total_lines': 10,
        'key_files': [],
        'dependencies': [],
        'frameworks': [],
        'project_name': 'Test',
    }
    
    doc_data = {
        'title': 'Test',
        'description': 'Test',
        'problem': '',
        'solution': '',
        'features': [],
        'installation': '',
        'usage': '',
    }
    
    generator = PresentationGenerator(code_analysis, doc_data)
    html = generator.generate()
    
    assert '<!DOCTYPE html>' in html
    assert '<html' in html
    assert '</html>' in html
    assert '<head>' in html
    assert '<body>' in html
    assert '<style>' in html


def test_generator_includes_keyboard_navigation():
    """Test that generator includes keyboard navigation script."""
    code_analysis = {
        'languages': {'Python': 1},
        'primary_language': 'Python',
        'file_count': 1,
        'total_lines': 10,
        'key_files': [],
        'dependencies': [],
        'frameworks': [],
        'project_name': 'Test',
    }
    
    doc_data = {
        'title': 'Test',
        'description': 'Test',
        'problem': '',
        'solution': '',
        'features': [],
        'installation': '',
        'usage': '',
    }
    
    generator = PresentationGenerator(code_analysis, doc_data)
    html = generator.generate()
    
    assert '<script>' in html
    assert 'keydown' in html or 'ArrowDown' in html


def test_generator_uses_custom_problem_and_solution():
    """Test that generator uses custom problem and solution when provided."""
    code_analysis = {
        'languages': {'Python': 1},
        'primary_language': 'Python',
        'file_count': 1,
        'total_lines': 10,
        'key_files': [],
        'dependencies': [],
        'frameworks': [],
        'project_name': 'Test',
    }
    
    doc_data = {
        'title': 'Custom Project',
        'description': 'Description',
        'problem': 'This is a custom problem statement',
        'solution': 'This is a custom solution approach',
        'features': ['Custom Feature 1', 'Custom Feature 2'],
        'installation': '',
        'usage': '',
    }
    
    generator = PresentationGenerator(code_analysis, doc_data)
    html = generator.generate()
    
    assert 'custom problem statement' in html
    assert 'custom solution approach' in html
    assert 'Custom Feature 1' in html
    assert 'Custom Feature 2' in html
