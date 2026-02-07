"""Presentation generator for creating hackathon slides."""
from jinja2 import Template
import os
from pathlib import Path
import random


class PresentationGenerator:
    """Generates a complete hackathon presentation."""

    # Default slide order (all available types)
    ALL_SLIDE_TYPES = [
        'title', 'problem', 'solution', 'demo',
        'impact', 'tech', 'future', 'closing',
    ]

    # Priority order for --max-slides (most important first)
    PRIORITY_ORDER = [
        'title', 'problem', 'solution', 'demo',
        'tech', 'closing', 'impact', 'future',
    ]

    def __init__(self, code_analysis, doc_data, theme_config=None,
                 slide_types=None, max_slides=None, html_template_path=None):
        self.code_analysis = code_analysis
        self.doc_data = doc_data
        self.theme_config = theme_config
        self.html_template_path = html_template_path
        self.slide_types = self._resolve_slide_types(slide_types, max_slides)
        self.code_snippets = self._extract_code_snippets()
        self.architecture_data = self._infer_architecture()

    def _resolve_slide_types(self, slide_types, max_slides):
        """Determine which slides to include based on user options."""
        if slide_types:
            # User explicitly listed which slides they want
            return [t for t in slide_types if t in self.ALL_SLIDE_TYPES]
        if max_slides and max_slides < len(self.ALL_SLIDE_TYPES):
            # Pick the top N by priority, then reorder to presentation flow
            selected = set(self.PRIORITY_ORDER[:max_slides])
            return [t for t in self.ALL_SLIDE_TYPES if t in selected]
        return list(self.ALL_SLIDE_TYPES)

    def _build_slides(self):
        """Build the slide list based on selected types."""
        generators = {
            'title': self._generate_title_slide,
            'problem': self._generate_problem_slide,
            'solution': self._generate_solution_slide,
            'demo': self._generate_demo_slide,
            'impact': self._generate_impact_slide,
            'tech': self._generate_tech_slide,
            'future': self._generate_future_slide,
            'closing': self._generate_closing_slide,
        }
        return [generators[t]() for t in self.slide_types]

    def _extract_code_snippets(self):
        """Extract meaningful code snippets from key files."""
        snippets = []
        key_files = self.code_analysis.get('key_files', [])
        
        for file_path in key_files[:3]:  # Top 3 key files
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Extract first interesting function/class
                        snippet = self._extract_interesting_snippet(content, file_path)
                        if snippet:
                            snippets.append(snippet)
            except Exception:
                pass
        
        return snippets
    
    def _extract_interesting_snippet(self, content, file_path):
        """Extract an interesting code snippet from file content."""
        lines = content.split('\n')
        ext = Path(file_path).suffix
        
        # Find first function/class definition
        for i, line in enumerate(lines):
            if ext in ['.py']:
                if line.strip().startswith('def ') or line.strip().startswith('class '):
                    # Extract 10 lines
                    snippet_lines = lines[i:min(i+10, len(lines))]
                    return {
                        'file': Path(file_path).name,
                        'language': 'python',
                        'code': '\n'.join(snippet_lines)
                    }
            elif ext in ['.js', '.ts', '.jsx', '.tsx']:
                if 'function ' in line or 'const ' in line and '=>' in line or 'class ' in line:
                    snippet_lines = lines[i:min(i+10, len(lines))]
                    return {
                        'file': Path(file_path).name,
                        'language': 'javascript',
                        'code': '\n'.join(snippet_lines)
                    }
            elif ext in ['.java']:
                if 'public class' in line or 'public void' in line:
                    snippet_lines = lines[i:min(i+10, len(lines))]
                    return {
                        'file': Path(file_path).name,
                        'language': 'java',
                        'code': '\n'.join(snippet_lines)
                    }
        
        return None
    
    def _infer_architecture(self):
        """Infer architecture based on code analysis."""
        frameworks = self.code_analysis.get('frameworks', [])
        dependencies = self.code_analysis.get('dependencies', [])
        primary_lang = self.code_analysis.get('primary_language', 'Unknown')
        
        # Detect common patterns
        has_db = any(dep in str(dependencies).lower() for dep in ['sql', 'mongo', 'postgres', 'mysql', 'redis', 'database'])
        has_api = any(dep in str(frameworks).lower() + str(dependencies).lower() for dep in ['express', 'fastapi', 'flask', 'rest', 'api', 'django'])
        has_frontend = any(fw in str(frameworks).lower() for fw in ['react', 'vue', 'angular', 'svelte'])
        
        return {
            'has_frontend': has_frontend,
            'has_api': has_api,
            'has_database': has_db,
            'primary_language': primary_lang,
            'frameworks': frameworks
        }

    def generate(self):
        """Generate the complete HTML presentation."""
        return self._render_html(self._build_slides())

    def get_slides_data(self):
        """Return raw slide data as a list of dicts (for JSON output)."""
        return self._build_slides()

    def _generate_title_slide(self):
        """Generate the title slide."""
        subtitle = self.doc_data.get('description', '')[:200]
        if not subtitle:
            primary_lang = self.code_analysis['primary_language']
            if primary_lang and primary_lang != 'Unknown':
                subtitle = f"A {primary_lang} project"
            else:
                subtitle = "An innovative software project"
            
        return {
            'type': 'title',
            'title': self.doc_data['title'],
            'subtitle': subtitle,
            'class': 'slide-title'
        }
    
    def _generate_problem_slide(self):
        """Generate the problem statement slide."""
        problem = self.doc_data.get('problem', '')
        if not problem:
            problem = f"Traditional solutions lack efficiency and modern capabilities. " \
                     f"We identified key challenges in the domain that need addressing."
        
        return {
            'type': 'content',
            'title': 'The Problem',
            'content': problem,
            'class': 'slide-problem'
        }
    
    def _generate_solution_slide(self):
        """Generate the solution slide."""
        solution = self.doc_data.get('solution', '')
        if not solution:
            primary_lang = self.code_analysis['primary_language']
            lang_text = f"leveraging {primary_lang}" if primary_lang and primary_lang != 'Unknown' else "using modern technology"
            solution = f"{self.doc_data['title']} provides an innovative solution " \
                      f"{lang_text} and modern architecture " \
                      f"to solve these challenges efficiently."
        
        return {
            'type': 'content',
            'title': 'Our Solution',
            'content': solution,
            'class': 'slide-solution'
        }
    
    def _generate_demo_slide(self):
        """Generate the demo/features slide."""
        features = list(self.doc_data.get('features', []))
        detected_features = self.code_analysis.get('features', [])

        # Merge detected features if not already in list
        for df in detected_features:
            if df not in features:
                features.append(df)

        if not features:
            primary_lang = self.code_analysis['primary_language']
            file_count = self.code_analysis.get('file_count', 0)
            total_lines = self.code_analysis.get('total_lines', 0)
            features = []
            if primary_lang and primary_lang != 'Unknown':
                features.append(f"Clean {primary_lang} implementation")
            if file_count > 0:
                features.append("Well-structured codebase")
                features.append(f"{file_count} files with {total_lines:,} lines of code")
            else:
                features.append("Innovative project concept")
            features.extend([
                "Modular and maintainable architecture",
                "Easy to deploy and use"
            ])

        return {
            'type': 'list',
            'title': 'Key Features',
            'list_items': features[:6],
            'class': 'slide-demo'
        }
    
    def _generate_impact_slide(self):
        """Generate the impact slide."""
        impact_points = self.doc_data.get('impact_points', [])
        
        if not impact_points:
            impact_points = [
                "Solves real-world problems efficiently",
                "Saves time and reduces complexity",
                "Improves user experience and productivity",
                "Scalable for future growth"
            ]
        
        return {
            'type': 'list',
            'title': 'Impact & Benefits',
            'list_items': impact_points,
            'class': 'slide-impact'
        }
    
    def _generate_tech_slide(self):
        """Generate the technology stack slide."""
        tech_items = []
        
        # Primary language
        primary_lang = self.code_analysis.get('primary_language', 'Unknown')
        if primary_lang and primary_lang != 'Unknown':
            tech_items.append(f"**Language:** {primary_lang}")
        
        # Show all languages if multiple
        languages = self.code_analysis.get('languages', {})
        if len(languages) > 1:
            lang_list = ', '.join([f"{lang} ({count})" for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]])
            tech_items.append(f"**Languages:** {lang_list}")
        
        # Frameworks
        if self.code_analysis['frameworks']:
            tech_items.append(f"**Frameworks:** {', '.join(self.code_analysis['frameworks'])}")
        
        # Key dependencies
        if self.code_analysis['dependencies']:
            deps = ', '.join(self.code_analysis['dependencies'][:5])
            tech_items.append(f"**Dependencies:** {deps}")
        
        # Project stats
        file_count = self.code_analysis['file_count']
        total_lines = self.code_analysis['total_lines']
        if file_count > 0:
            tech_items.append(f"**Scale:** {file_count} files, {total_lines:,} lines")
        
        # If no tech info, add generic items
        if not tech_items:
            tech_items = [
                "**Modern Architecture**: Built with best practices",
                "**Scalable Design**: Ready for growth",
                "**Well-Documented**: Clear and comprehensive"
            ]
        
        slide_data = {
            'type': 'tech',
            'title': 'Technology Stack',
            'list_items': tech_items,
            'class': 'slide-tech',
            'code_snippets': self.code_snippets[:2],  # Include up to 2 code snippets
            'languages': languages,
            'architecture': self.architecture_data
        }
        
        return slide_data
    
    def _generate_future_slide(self):
        """Generate the future plans slide."""
        future_items = [
            "Enhance features based on user feedback",
            "Optimize performance and scalability",
            "Expand platform compatibility",
            "Build community and ecosystem",
            "Add advanced analytics and insights"
        ]
        
        return {
            'type': 'list',
            'title': 'Future Plans',
            'list_items': future_items,
            'class': 'slide-future'
        }
    
    def _generate_closing_slide(self):
        """Generate the closing slide."""
        return {
            'type': 'closing',
            'title': 'Thank You!',
            'subtitle': f'{self.doc_data["title"]} - Built with {self.code_analysis["primary_language"]}',
            'class': 'slide-closing'
        }
    
    def _render_html(self, slides):
        """Render slides into enhanced Reveal.js HTML with code highlighting and visualizations."""
        slide_html = ""
        for slide in slides:
            type_ = slide.get('type')
            title = slide.get('title', '')
            
            if type_ == 'title':
                slide_html += f"""
                <section data-background-gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
                    <h1 class="r-fit-text">{title}</h1>
                    <h3 class="fragment fade-up">{slide.get('subtitle', '')}</h3>
                </section>"""
            elif type_ == 'tech':
                # Enhanced tech slide with code snippets and architecture
                items = "".join([f"<li class='fragment'>{item}</li>" for item in slide.get('list_items', [])])
                
                # Generate architecture diagram
                arch = slide.get('architecture', {})
                mermaid_diagram = self._generate_architecture_diagram(arch)
                
                # Add code snippets if available
                code_section = ""
                if slide.get('code_snippets'):
                    for snippet in slide.get('code_snippets', [])[:1]:  # Show first snippet
                        code_section += f"""
                        <div class="code-snippet fragment">
                            <div class="code-header">{snippet['file']}</div>
                            <pre><code class="language-{snippet['language']}">{self._escape_html(snippet['code'])}</code></pre>
                        </div>
                        """
                
                # Language distribution chart data
                lang_data = slide.get('languages', {})
                lang_chart_data = self._generate_language_chart_data(lang_data)
                
                slide_html += f"""
                <section>
                    <h2>{title}</h2>
                    <div class="tech-layout">
                        <div class="tech-info">
                            <ul>{items}</ul>
                        </div>
                        <div class="tech-visual">
                            <div class="architecture-diagram">
                                <div class="mermaid">{mermaid_diagram}</div>
                            </div>
                            {f'<canvas id="langChart" class="lang-chart"></canvas>' if lang_data else ''}
                        </div>
                    </div>
                    {code_section}
                </section>
                <script>
                    {lang_chart_data}
                </script>
                """
            elif type_ == 'list' or type_ == 'demo' or type_ == 'future':
                items = "".join([f"<li class='fragment'>{item}</li>" for item in slide.get('list_items', [])])
                slide_html += f"""
                <section>
                    <h2>{title}</h2>
                    <ul class="feature-list">{items}</ul>
                </section>"""
            elif type_ == 'content' or type_ == 'problem' or type_ == 'solution':
                slide_html += f"""
                <section>
                    <h2>{title}</h2>
                    <div class="content-box fragment">
                        <p>{slide.get('content', '')}</p>
                    </div>
                </section>"""
            elif type_ == 'closing':
                slide_html += f"""
                <section data-background-gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
                    <h1>{title}</h1>
                    <p class="closing-subtitle">{slide.get('subtitle', '')}</p>
                    <small class="generator-credit">Generated by MindCore · Luminary</small>
                </section>"""

        return f"""
<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <title>{self.doc_data['title']} - MindCore Presentation</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/reveal.css">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/theme/black.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-javascript.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-java.min.js"></script>
        <style>
            .reveal h1, .reveal h2, .reveal h3 {{
                text-transform: none;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }}
            
            .tech-layout {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 2rem;
                margin-top: 2rem;
            }}
            
            .tech-info ul {{
                text-align: left;
                font-size: 0.9em;
            }}
            
            .tech-visual {{
                display: flex;
                flex-direction: column;
                gap: 1rem;
            }}
            
            .architecture-diagram .mermaid {{
                background: rgba(255, 255, 255, 0.95);
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }}
            
            .code-snippet {{
                margin-top: 2rem;
                text-align: left;
            }}
            
            .code-header {{
                background: #2d2d2d;
                color: #61dafb;
                padding: 0.5rem 1rem;
                border-radius: 8px 8px 0 0;
                font-family: 'Monaco', 'Courier New', monospace;
                font-size: 0.8em;
            }}
            
            .code-snippet pre {{
                margin: 0 !important;
                border-radius: 0 0 8px 8px !important;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
            }}
            
            .code-snippet code {{
                font-size: 0.7em !important;
                line-height: 1.5 !important;
            }}
            
            .lang-chart {{
                max-height: 300px;
                background: rgba(255, 255, 255, 0.1);
                padding: 1rem;
                border-radius: 12px;
            }}
            
            .feature-list {{
                column-count: 2;
                column-gap: 3rem;
                text-align: left;
            }}
            
            .feature-list li {{
                margin-bottom: 1rem;
                break-inside: avoid;
            }}
            
            .content-box {{
                background: rgba(255, 255, 255, 0.05);
                padding: 2rem;
                border-radius: 12px;
                border-left: 4px solid #667eea;
                margin: 2rem auto;
                max-width: 800px;
            }}
            
            .content-box p {{
                font-size: 1.3em;
                line-height: 1.8;
                text-align: left;
            }}
            
            .closing-subtitle {{
                font-size: 1.2em;
                margin: 2rem 0;
            }}
            
            .generator-credit {{
                opacity: 0.6;
                margin-top: 3rem;
                display: block;
            }}
            
            @media (max-width: 768px) {{
                .tech-layout {{
                    grid-template-columns: 1fr;
                }}
                .feature-list {{
                    column-count: 1;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="reveal">
            <div class="slides">
                {slide_html}
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/reveal.js"></script>
        <script>
            Reveal.initialize({{
                controls: true,
                progress: true,
                center: true,
                hash: true,
                transition: 'slide',
                autoAnimate: true,
                backgroundTransition: 'fade'
            }});
            
            Reveal.addEventListener('ready', function() {{
                mermaid.initialize({{ 
                    startOnLoad: true, 
                    theme: 'default',
                    themeVariables: {{
                        fontSize: '16px'
                    }}
                }});
                
                // Trigger Prism highlighting
                if (typeof Prism !== 'undefined') {{
                    Prism.highlightAll();
                }}
            }});
        </script>
    </body>
</html>"""
    
    def _generate_architecture_diagram(self, arch_data):
        """Generate Mermaid architecture diagram based on project analysis."""
        has_frontend = arch_data.get('has_frontend', False)
        has_api = arch_data.get('has_api', False)
        has_db = arch_data.get('has_database', False)
        
        if has_frontend and has_api and has_db:
            return """
                graph TB
                    A[User/Client] --> B[Frontend Layer]
                    B --> C[API/Backend]
                    C --> D[(Database)]
                    C --> E[External Services]
                    style A fill:#667eea
                    style B fill:#48c774
                    style C fill:#3298dc
                    style D fill:#f14668
                    style E fill:#ffdd57
            """
        elif has_api and has_db:
            return """
                graph LR
                    A[Client] --> B[API Server]
                    B --> C[(Database)]
                    B --> D[Cache]
                    style A fill:#667eea
                    style B fill:#3298dc
                    style C fill:#f14668
                    style D fill:#ffdd57
            """
        elif has_frontend and has_api:
            return """
                graph LR
                    A[User Interface] --> B[REST API]
                    B --> C[Business Logic]
                    C --> D[Data Layer]
                    style A fill:#48c774
                    style B fill:#3298dc
                    style C fill:#667eea
                    style D fill:#f14668
            """
        else:
            # Simple generic architecture
            return """
                graph TB
                    A[Application] --> B[Core Logic]
                    B --> C[Data/Resources]
                    style A fill:#667eea
                    style B fill:#3298dc
                    style C fill:#f14668
            """
    
    def _generate_language_chart_data(self, lang_data):
        """Generate Chart.js data for language distribution."""
        if not lang_data:
            return ""
        
        labels = list(lang_data.keys())[:5]  # Top 5 languages
        data = [lang_data[lang] for lang in labels]
        colors = ['#667eea', '#48c774', '#3298dc', '#ffdd57', '#f14668']
        
        return f"""
            if (document.getElementById('langChart')) {{
                const ctx = document.getElementById('langChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'doughnut',
                    data: {{
                        labels: {labels},
                        datasets: [{{
                            data: {data},
                            backgroundColor: {colors[:len(labels)]},
                            borderWidth: 2,
                            borderColor: '#1a1a1a'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'right',
                                labels: {{
                                    color: '#ffffff',
                                    font: {{
                                        size: 14
                                    }}
                                }}
                            }},
                            title: {{
                                display: true,
                                text: 'Language Distribution',
                                color: '#ffffff',
                                font: {{
                                    size: 16
                                }}
                            }}
                        }}
                    }}
                }});
            }}
        """
    
    def _escape_html(self, text):
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    def generate_markdown(self):
        """Generate a Marp-compatible Markdown presentation."""
        slides = self._build_slides()
        markdown = ["---\nmarp: true\ntheme: default\npaginate: true\n---\n\n"]

        for slide in slides:
            title = slide.get('title', '')
            markdown.append("---\n\n")

            if slide.get('type') in ['title', 'closing']:
                markdown.append(f"# {title}\n\n{slide.get('subtitle', '')}\n")
                continue

            markdown.append(f"## {title}\n\n")
            if slide.get('type') == 'content':
                markdown.append(f"{slide.get('content', '')}\n")
            elif slide.get('type') == 'list':
                for item in slide.get('list_items', []):
                    markdown.append(f"- {item}\n")

        return ''.join(markdown)
    
    def _get_html_template(self):
        """Get the HTML template for the presentation."""
        if self.html_template_path:
            from pathlib import Path
            try:
                return Path(self.html_template_path).read_text(encoding='utf-8')
            except Exception as e:
                print(f"Warning: Failed to load template from {self.html_template_path}: {e}")
                # Fall through to default

        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ project_name }} - Hackathon Presentation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #0f0f0f;
            color: #ffffff;
            overflow-x: hidden;
        }
        
        .presentation {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        
        .slide {
            min-height: 80vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 60px;
            margin-bottom: 40px;
            border-radius: 20px;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            position: relative;
            overflow: hidden;
        }
        
        .slide::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        }
        
        .slide-title {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .slide-problem {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .slide-solution {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        .slide-demo {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }
        
        .slide-impact {
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }
        
        .slide-tech {
            background: linear-gradient(135deg, #30cfd0 0%, #330867 100%);
        }
        
        .slide-future {
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            color: #1a1a2e;
        }
        
        .slide-closing {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .slide h1 {
            font-size: 4rem;
            font-weight: 800;
            margin-bottom: 30px;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .slide h2 {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 40px;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .slide-content {
            font-size: 1.5rem;
            line-height: 2;
            max-width: 900px;
            text-align: center;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
        }
        
        .slide-list {
            list-style: none;
            font-size: 1.5rem;
            line-height: 2.5;
            max-width: 900px;
            width: 100%;
        }
        
        .slide-list li {
            padding: 15px 20px;
            margin: 10px 0;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            backdrop-filter: blur(10px);
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
            border-left: 4px solid rgba(255, 255, 255, 0.3);
        }
        
        .slide-future .slide-list li {
            background: rgba(0, 0, 0, 0.1);
            border-left-color: rgba(0, 0, 0, 0.3);
        }
        
        .subtitle {
            font-size: 1.8rem;
            font-weight: 400;
            opacity: 0.9;
            text-align: center;
            max-width: 800px;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
        }
        
        .slide-number {
            position: absolute;
            bottom: 30px;
            right: 40px;
            font-size: 1.2rem;
            opacity: 0.6;
        }
        
        @media print {
            .slide {
                page-break-after: always;
                min-height: 100vh;
                margin-bottom: 0;
            }
        }
        
        @media (max-width: 768px) {
            .slide {
                padding: 40px 20px;
            }
            
            .slide h1 {
                font-size: 2.5rem;
            }
            
            .slide h2 {
                font-size: 2rem;
            }
            
            .slide-content, .slide-list {
                font-size: 1.2rem;
            }
            
            .subtitle {
                font-size: 1.3rem;
            }
        }
        
        strong {
            color: rgba(255, 255, 255, 0.95);
            font-weight: 700;
        }
        
        .slide-future strong {
            color: rgba(0, 0, 0, 0.9);
        }
    </style>
</head>
<body>
    <div class="presentation">
        {% for slide in slides %}
        <div class="slide {{ slide.class }}">
            {% if slide.type == 'title' %}
                <h1>{{ slide.title }}</h1>
                <p class="subtitle">{{ slide.subtitle }}</p>
            {% elif slide.type == 'content' %}
                <h2>{{ slide.title }}</h2>
                <p class="slide-content">{{ slide.content }}</p>
            {% elif slide.type == 'list' %}
                <h2>{{ slide.title }}</h2>
                <ul class="slide-list">
                    {% for item in slide.list_items %}
                    <li>{{ item }}</li>
                    {% endfor %}
                </ul>
            {% elif slide.type == 'closing' %}
                <h1>{{ slide.title }}</h1>
                <p class="subtitle">{{ slide.subtitle }}</p>
            {% endif %}
            <div class="slide-number">{{ loop.index }} / {{ total_slides }}</div>
        </div>
        {% endfor %}
    </div>
    
    <script>
        // Keyboard navigation
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');
        
        function scrollToSlide(index) {
            if (index >= 0 && index < slides.length) {
                slides[index].scrollIntoView({ behavior: 'smooth', block: 'center' });
                currentSlide = index;
            }
        }
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowDown' || e.key === 'ArrowRight' || e.key === ' ') {
                e.preventDefault();
                scrollToSlide(currentSlide + 1);
            } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
                e.preventDefault();
                scrollToSlide(currentSlide - 1);
            } else if (e.key === 'Home') {
                e.preventDefault();
                scrollToSlide(0);
            } else if (e.key === 'End') {
                e.preventDefault();
                scrollToSlide(slides.length - 1);
            }
        });
        
        // Track which slide is in view
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    currentSlide = Array.from(slides).indexOf(entry.target);
                }
            });
        }, { threshold: 0.5 });
        
        slides.forEach(slide => observer.observe(slide));
    </script>
</body>
</html>'''
