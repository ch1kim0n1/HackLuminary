# HackLuminary

**CLI-first, local-only, deterministic tool for generating hackathon presentations**

MindCore's open source hackathon-oriented software. It analyzes your codebase and documentation to create a full presentation with graphics and slides, following hackathon presentation requirements and chronological order.

## Features

- ✅ **CLI-First**: Simple command-line interface, no GUI required
- ✅ **Local-Only**: Runs entirely on your machine, no cloud dependencies
- ✅ **Deterministic**: Same input always produces the same output
- ✅ **No 3rd Party APIs**: Works completely offline
- ✅ **Fail-Fast**: Clear error messages on missing or invalid data
- ✅ **Hackathon-Ready**: Follows standard judging flow (Problem → Solution → Demo → Impact → Tech → Future)
- ✅ **Multi-Language Support**: Analyzes Python, JavaScript, TypeScript, Java, Go, Rust, and more
- ✅ **Beautiful Output**: Generates modern, visually appealing HTML presentations

## Installation

```bash
# Clone the repository
git clone https://github.com/ch1kim0n1/HackLuminary.git
cd HackLuminary

# Install the package
pip install -e .
```

## Usage

### Basic Usage

Generate a presentation from your project directory:

```bash
hackluminary --project-dir /path/to/your/project
```

This will create a `presentation.html` file in the current directory.

### Custom Output Path

Specify a custom output file:

```bash
hackluminary --project-dir /path/to/your/project --output my-presentation.html
```

### Auto-Open in Browser

Generate and automatically open the presentation:

```bash
hackluminary --project-dir /path/to/your/project --open
```

### Select Specific Slides

Choose which slides to include:

```bash
# Include only title, problem, solution, and demo slides
hackluminary --project-dir /path/to/your/project --slides title,problem,solution,demo
```

Available slide types: `title`, `problem`, `solution`, `demo`, `impact`, `tech`, `future`, `closing`

### Limit Number of Slides

Automatically select the most important slides:

```bash
# Generate a 5-slide presentation (picks most important slides)
hackluminary --project-dir /path/to/your/project --max-slides 5
```

### Include Additional Documentation

Include additional documentation files:

```bash
hackluminary --project-dir /path/to/your/project --docs OVERVIEW.md --docs TECHNICAL.md
```

### Example

```bash
# Generate presentation for the HackLuminary project itself
hackluminary --project-dir . --output hackluminary-presentation.html

# Generate and auto-open in browser
hackluminary --project-dir . --output hackluminary-presentation.html --open

# Generate a quick 5-slide pitch deck
hackluminary --project-dir . --max-slides 5 --open

# Custom slide selection for investor pitch
hackluminary --project-dir . --slides title,problem,solution,impact,closing --open
```

## Presentation Structure

The generated presentation follows the standard hackathon judging flow:

1. **Title Slide**: Project name and description
2. **Problem**: The challenge being addressed
3. **Solution**: How your project solves the problem
4. **Demo/Features**: Key features and capabilities
5. **Impact**: Benefits and real-world impact
6. **Technology Stack**: Languages, frameworks, and tools used
7. **Future Plans**: Roadmap and next steps
8. **Closing**: Thank you slide

## How It Works

1. **Codebase Analysis**: Scans your project directory to identify:
   - Programming languages used
   - Frameworks and dependencies
   - Project structure and scale
   - Key files and entry points

2. **Documentation Parsing**: Extracts information from:
   - README.md (title, description, features, etc.)
   - Additional documentation files
   - Problem/solution statements
   - Installation and usage instructions

3. **Presentation Generation**: Creates a complete HTML presentation with:
   - Beautiful gradient backgrounds
   - Clear typography and layout
   - Keyboard navigation (arrow keys, space)
   - Responsive design
   - Print-friendly formatting

## Keyboard Navigation

Once you open the presentation in a browser:

- **Arrow Down / Right / Space**: Next slide
- **Arrow Up / Left**: Previous slide
- **Home**: First slide
- **End**: Last slide

## Requirements

- Python 3.8+
- No internet connection required
- No external APIs or cloud services

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest

# Run tests
pytest tests/ -v
```

### Project Structure

```
HackLuminary/
├── hackluminary/           # Main package
│   ├── __init__.py
│   ├── cli.py             # CLI interface
│   ├── analyzer.py        # Codebase analyzer
│   ├── document_parser.py # Documentation parser
│   └── presentation_generator.py # HTML generator
├── tests/                  # Test suite
│   ├── test_analyzer.py
│   ├── test_document_parser.py
│   └── test_presentation_generator.py
├── setup.py               # Package configuration
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## Design Principles

### 1. CLI-First

- Command-line interface is the primary way to interact
- Simple, intuitive command structure
- Clear help text and error messages

### 2. Local-Only

- All processing happens on your machine
- No data sent to external services
- Works completely offline

### 3. Deterministic

- Same input always produces same output
- No randomness or variability
- Predictable and reliable

### 4. No 3rd Party APIs

- No dependencies on external services
- No API keys or authentication required
- Complete privacy and security

### 5. Fail-Fast

- Validates inputs immediately
- Clear error messages
- Fails early on missing or invalid data

### 6. Immediately Usable Output

- Generates ready-to-use HTML files
- No post-processing required
- Open directly in any browser

## Supported Languages

HackLuminary can analyze projects written in:

- Python (.py)
- JavaScript (.js)
- TypeScript (.ts, .tsx)
- React (.jsx, .tsx)
- Java (.java)
- C/C++ (.c, .cpp)
- C# (.cs)
- Go (.go)
- Rust (.rs)
- Ruby (.rb)
- PHP (.php)
- Swift (.swift)
- Kotlin (.kt)
- HTML/CSS (.html, .css, .scss)
- Vue (.vue)
- SQL (.sql)

## Supported Dependency Files

- **JavaScript/TypeScript**: package.json
- **Python**: requirements.txt
- **Go**: go.mod
- **Rust**: Cargo.toml

## Troubleshooting

### Error: Project directory does not exist

Make sure the path you provide exists and is accessible.

### Error: Failed to analyze codebase - no recognizable code found

Ensure your project directory contains code files with supported extensions.

### Presentation looks broken

Make sure you're opening the HTML file in a modern web browser (Chrome, Firefox, Safari, Edge).

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.
