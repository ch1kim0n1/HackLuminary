"""Codebase analyzer for extracting project information."""
import os
from pathlib import Path
from collections import defaultdict
import re


class CodebaseAnalyzer:
    """Analyzes a codebase to extract key information."""
    
    LANGUAGE_EXTENSIONS = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'React',
        '.tsx': 'React/TypeScript',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.cs': 'C#',
        '.go': 'Go',
        '.rs': 'Rust',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'Sass',
        '.vue': 'Vue',
        '.sql': 'SQL',
        '.scala': 'Scala',
        '.r': 'R',
        '.m': 'MATLAB/Objective-C',
        '.h': 'C/C++ Header',
        '.hpp': 'C++ Header',
        '.pl': 'Perl',
        '.sh': 'Shell',
        '.bash': 'Bash',
        '.ps1': 'PowerShell',
        '.dart': 'Dart',
        '.lua': 'Lua',
        '.clj': 'Clojure',
        '.ex': 'Elixir',
        '.exs': 'Elixir',
        '.erl': 'Erlang',
        '.hrl': 'Erlang',
        '.hs': 'Haskell',
        '.ml': 'OCaml',
        '.elm': 'Elm',
        '.jl': 'Julia',
        '.nim': 'Nim',
        '.v': 'V/Verilog',
        '.vhd': 'VHDL',
        '.vhdl': 'VHDL',
        '.xml': 'XML',
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.toml': 'TOML',
        '.md': 'Markdown',
        '.rst': 'reStructuredText',
        '.tex': 'LaTeX',
    }
    
    # Common code file extensions for generic detection
    CODE_EXTENSIONS = {
        '.txt', '.cfg', '.conf', '.ini', '.properties',
        '.gradle', '.gradle.kts', '.sbt', '.pom'
    }
    
    IGNORE_DIRS = {
        'node_modules', '.git', '__pycache__', 'venv', 'env', 
        'dist', 'build', '.pytest_cache', 'coverage', '.idea',
        'vendor', 'target', 'bin', 'obj', '.vscode'
    }
    
    KEY_FILE_NAMES = {
        'main.py', 'app.py', 'index.js', 'main.js', 
        'App.js', 'index.html', 'server.py', 'main.go',
        'main.rs', 'main.cpp', 'main.c', 'main.java',
        'index.php', 'main.rb', 'server.js', 'app.js'
    }
    
    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.languages = defaultdict(int)
        self.file_count = 0
        self.total_lines = 0
        self.key_files = []
        self.dependencies = []
        self.frameworks = []
        
    def analyze(self):
        """Analyze the entire codebase."""
        self._scan_directory(self.project_path)
        self._detect_frameworks()
        self._detect_dependencies()
        
        # Always return a result, even if no code files found
        # This ensures the tool works with ANY project
        primary_lang = self._get_primary_language()
        
        return {
            'languages': dict(self.languages),
            'primary_language': primary_lang,
            'file_count': self.file_count,
            'total_lines': self.total_lines,
            'key_files': self.key_files,
            'dependencies': self.dependencies,
            'frameworks': self.frameworks,
            'project_name': self.project_path.name,
        }
    
    def _scan_directory(self, directory):
        """Recursively scan directory for code files."""
        try:
            for item in directory.iterdir():
                if item.is_dir() and item.name not in self.IGNORE_DIRS:
                    self._scan_directory(item)
                elif item.is_file():
                    self._analyze_file(item)
        except PermissionError:
            pass
    
    def _analyze_file(self, file_path):
        """Analyze a single file."""
        ext = file_path.suffix.lower()
        
        # Skip binary and generated files
        skip_extensions = {'.pyc', '.pyo', '.exe', '.dll', '.so', '.dylib', 
                          '.class', '.jar', '.war', '.ear', '.o', '.a',
                          '.pdf', '.doc', '.docx', '.xls', '.xlsx',
                          '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg',
                          '.mp3', '.mp4', '.avi', '.mov', '.zip', '.tar', '.gz'}
        
        if ext in skip_extensions:
            return
        
        # Analyze recognized languages
        if ext in self.LANGUAGE_EXTENSIONS:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = len(content.splitlines())
                    
                self.languages[self.LANGUAGE_EXTENSIONS[ext]] += 1
                self.file_count += 1
                self.total_lines += lines
                
                # Track key files
                if file_path.name in self.KEY_FILE_NAMES:
                    self.key_files.append(str(file_path.relative_to(self.project_path)))
                    
            except Exception:
                pass
        # Also count files with common code-related extensions or no extension
        elif ext in self.CODE_EXTENSIONS or (ext == '' and not file_path.name.startswith('.')):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Basic heuristic: if file has reasonable content, count it
                    if content.strip() and len(content) < 1000000:  # Skip very large files
                        lines = len(content.splitlines())
                        if lines > 0:
                            self.languages['Other'] += 1
                            self.file_count += 1
                            self.total_lines += lines
            except Exception:
                pass
    
    def _get_primary_language(self):
        """Determine the primary programming language."""
        if not self.languages:
            return "Unknown"
        return max(self.languages.items(), key=lambda x: x[1])[0]
    
    def _detect_frameworks(self):
        """Detect frameworks used in the project."""
        # Check for common framework indicators
        framework_files = {
            'package.json': ['React', 'Vue', 'Angular', 'Express', 'Next.js'],
            'requirements.txt': ['Django', 'Flask', 'FastAPI'],
            'Gemfile': ['Rails', 'Sinatra'],
            'pom.xml': ['Spring', 'Hibernate'],
            'go.mod': ['Gin', 'Echo'],
            'Cargo.toml': ['Actix', 'Rocket'],
        }
        
        for file_name, possible_frameworks in framework_files.items():
            file_path = self.project_path / file_name
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    for framework in possible_frameworks:
                        if framework.lower() in content.lower():
                            if framework not in self.frameworks:
                                self.frameworks.append(framework)
                except Exception:
                    pass
    
    def _detect_dependencies(self):
        """Detect project dependencies."""
        dep_files = {
            'package.json': self._parse_package_json,
            'requirements.txt': self._parse_requirements_txt,
            'go.mod': self._parse_go_mod,
            'Cargo.toml': self._parse_cargo_toml,
        }
        
        for file_name, parser in dep_files.items():
            file_path = self.project_path / file_name
            if file_path.exists():
                try:
                    parser(file_path)
                except Exception:
                    pass
    
    def _parse_package_json(self, file_path):
        """Parse package.json for dependencies."""
        import json
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                deps = list(data.get('dependencies', {}).keys())
                self.dependencies.extend(deps[:10])  # Limit to top 10
        except Exception:
            pass
    
    def _parse_requirements_txt(self, file_path):
        """Parse requirements.txt for dependencies."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        pkg = re.split(r'[>=<]', line)[0].strip()
                        if pkg:
                            self.dependencies.append(pkg)
                            if len(self.dependencies) >= 10:
                                break
        except Exception:
            pass
    
    def _parse_go_mod(self, file_path):
        """Parse go.mod for dependencies."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('require'):
                        continue
                    match = re.match(r'\s+([^\s]+)', line)
                    if match:
                        self.dependencies.append(match.group(1))
                        if len(self.dependencies) >= 10:
                            break
        except Exception:
            pass
    
    def _parse_cargo_toml(self, file_path):
        """Parse Cargo.toml for dependencies."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                in_deps = False
                for line in f:
                    if '[dependencies]' in line:
                        in_deps = True
                        continue
                    if in_deps and line.strip().startswith('['):
                        break
                    if in_deps and '=' in line:
                        pkg = line.split('=')[0].strip()
                        if pkg:
                            self.dependencies.append(pkg)
                            if len(self.dependencies) >= 10:
                                break
        except Exception:
            pass
