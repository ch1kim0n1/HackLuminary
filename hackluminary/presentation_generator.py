"""Presentation generator for creating hackathon slides."""
from jinja2 import Template


class PresentationGenerator:
    """Generates a complete hackathon presentation."""
    
    def __init__(self, code_analysis, doc_data):
        self.code_analysis = code_analysis
        self.doc_data = doc_data
        
    def generate(self):
        """Generate the complete HTML presentation."""
        slides = []
        
        # Slide 1: Title
        slides.append(self._generate_title_slide())
        
        # Slide 2: Problem
        slides.append(self._generate_problem_slide())
        
        # Slide 3: Solution
        slides.append(self._generate_solution_slide())
        
        # Slide 4: Demo/Features
        slides.append(self._generate_demo_slide())
        
        # Slide 5: Impact
        slides.append(self._generate_impact_slide())
        
        # Slide 6: Technology Stack
        slides.append(self._generate_tech_slide())
        
        # Slide 7: Future Plans
        slides.append(self._generate_future_slide())
        
        # Slide 8: Thank You
        slides.append(self._generate_closing_slide())
        
        return self._render_html(slides)
    
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
            'title': '🎯 The Problem',
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
            'title': '💡 Our Solution',
            'content': solution,
            'class': 'slide-solution'
        }
    
    def _generate_demo_slide(self):
        """Generate the demo/features slide."""
        features = self.doc_data.get('features', [])
        if not features:
            primary_lang = self.code_analysis['primary_language']
            file_count = self.code_analysis['file_count']
            total_lines = self.code_analysis['total_lines']
            
            features = []
            if primary_lang and primary_lang != 'Unknown':
                features.append(f"Clean {primary_lang} implementation")
            elif file_count > 0:
                features.append("Well-structured codebase")
            else:
                features.append("Innovative project concept")
                
            if file_count > 0:
                features.append(f"{file_count} files with {total_lines:,} lines of code")
            
            features.extend([
                "Modular and maintainable architecture",
                "Easy to deploy and use"
            ])
        
        return {
            'type': 'list',
            'title': '🚀 Key Features',
            'list_items': features,
            'class': 'slide-demo'
        }
    
    def _generate_impact_slide(self):
        """Generate the impact slide."""
        impact_points = [
            "Solves real-world problems efficiently",
            "Saves time and reduces complexity",
            "Improves user experience and productivity",
            "Scalable for future growth"
        ]
        
        return {
            'type': 'list',
            'title': '📈 Impact & Benefits',
            'list_items': impact_points,
            'class': 'slide-impact'
        }
    
    def _generate_tech_slide(self):
        """Generate the technology stack slide."""
        tech_items = []
        
        # Primary language
        primary_lang = self.code_analysis['primary_language']
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
        
        return {
            'type': 'list',
            'title': '🔧 Technology Stack',
            'list_items': tech_items,
            'class': 'slide-tech'
        }
    
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
            'title': '🔮 Future Plans',
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
        """Render slides into HTML."""
        template = Template(self._get_html_template())
        return template.render(slides=slides, project_name=self.doc_data['title'], 
                               total_slides=len(slides))
    
    def _get_html_template(self):
        """Get the HTML template for the presentation."""
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
