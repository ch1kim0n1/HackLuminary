"""Document parser for extracting information from documentation files."""
import re
from pathlib import Path


class DocumentParser:
    """Parses documentation to extract project information."""
    
    def __init__(self, project_path, additional_docs=None):
        self.project_path = Path(project_path)
        self.additional_docs = additional_docs or []
        
    def parse(self):
        """Parse all available documentation."""
        doc_data = {
            'title': self.project_path.name,
            'description': '',
            'problem': '',
            'solution': '',
            'features': [],
            'installation': '',
            'usage': '',
        }
        
        # Try to find README
        readme_path = self._find_readme()
        if readme_path:
            self._parse_readme(readme_path, doc_data)
        
        # Parse additional docs
        for doc_path in self.additional_docs:
            self._parse_additional_doc(Path(doc_path), doc_data)
        
        return doc_data
    
    def _find_readme(self):
        """Find README file in project directory."""
        possible_names = ['README.md', 'README.txt', 'README', 'readme.md', 'Readme.md']
        for name in possible_names:
            path = self.project_path / name
            if path.exists():
                return path
        return None
    
    def _parse_readme(self, readme_path, doc_data):
        """Parse README file."""
        try:
            content = readme_path.read_text(encoding='utf-8', errors='ignore')
            
            # Extract title (first # heading)
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                doc_data['title'] = title_match.group(1).strip()
            
            # Extract description (text after title, before next heading)
            desc_match = re.search(r'^#\s+.+?\n\n(.+?)(?=\n#|\n##|\Z)', content, re.MULTILINE | re.DOTALL)
            if desc_match:
                doc_data['description'] = desc_match.group(1).strip()[:500]
            
            # Look for problem section
            problem_match = re.search(r'##?\s+(?:Problem|Challenge|Issue|Motivation)\s*\n(.+?)(?=\n#|\Z)', 
                                      content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
            if problem_match:
                doc_data['problem'] = problem_match.group(1).strip()[:500]
            
            # Look for solution section
            solution_match = re.search(r'##?\s+(?:Solution|Approach|How it Works)\s*\n(.+?)(?=\n#|\Z)', 
                                        content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
            if solution_match:
                doc_data['solution'] = solution_match.group(1).strip()[:500]
            
            # Extract features (bullet points)
            features_match = re.search(r'##?\s+(?:Features|Functionality|Capabilities)\s*\n(.+?)(?=\n#|\Z)', 
                                        content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
            if features_match:
                features_text = features_match.group(1)
                # Extract bullet points
                features = re.findall(r'^[\*\-]\s+(.+)$', features_text, re.MULTILINE)
                doc_data['features'] = [f.strip() for f in features[:8]]
            
            # Extract installation instructions
            install_match = re.search(r'##?\s+(?:Installation|Setup|Getting Started)\s*\n(.+?)(?=\n#|\Z)', 
                                      content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
            if install_match:
                doc_data['installation'] = install_match.group(1).strip()[:300]
            
            # Extract usage
            usage_match = re.search(r'##?\s+(?:Usage|How to Use|Examples)\s*\n(.+?)(?=\n#|\Z)', 
                                     content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
            if usage_match:
                doc_data['usage'] = usage_match.group(1).strip()[:300]
                
        except Exception:
            pass
    
    def _parse_additional_doc(self, doc_path, doc_data):
        """Parse additional documentation file."""
        try:
            content = doc_path.read_text(encoding='utf-8', errors='ignore')
            # Add to description if not too long
            if len(doc_data['description']) < 300:
                doc_data['description'] += '\n\n' + content[:200]
        except Exception:
            pass
