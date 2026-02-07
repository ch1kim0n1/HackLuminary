# HackLuminary Examples

This document shows examples of using HackLuminary to generate hackathon presentations.

## Example 1: Basic Usage

Generate a presentation for your project:

```bash
cd /path/to/your/project
hackluminary --project-dir .
```

This creates `presentation.html` in the current directory.

## Example 2: Custom Output Path

```bash
hackluminary --project-dir ./my-app --output demo-day-presentation.html
```

## Example 3: Auto-Open in Browser

Generate and immediately view the presentation:

```bash
hackluminary --project-dir . --output pitch.html --open
```

## Example 4: Quick 5-Slide Pitch

Generate a concise presentation with only the most important slides:

```bash
hackluminary --project-dir . --max-slides 5 --open
```

This automatically selects: title, problem, solution, demo, tech, and closing (in priority order).

## Example 5: Custom Slide Selection

Choose exactly which slides to include:

```bash
# Investor pitch (problem-focused)
hackluminary --project-dir . --slides title,problem,solution,impact,closing

# Technical demo (tech-focused)
hackluminary --project-dir . --slides title,demo,tech,future,closing

# Quick overview (minimal)
hackluminary --project-dir . --slides title,solution,demo,closing
```

Available slide types:

- `title` - Project name and description
- `problem` - Problem statement
- `solution` - Your solution
- `demo` - Key features
- `impact` - Benefits and impact
- `tech` - Technology stack
- `future` - Future plans
- `closing` - Thank you slide

## Example 6: With Additional Documentation

```bash
hackluminary --project-dir . \
  --docs ARCHITECTURE.md \
  --docs TECHNICAL_OVERVIEW.md \
  --output full-presentation.html
```

## Example 4: Multi-Language Project

For a project using multiple languages (e.g., Python backend + React frontend):

```bash
hackluminary --project-dir . --output tech-stack-presentation.html
```

HackLuminary will automatically:

- Detect Python files in `/backend` or `/server`
- Detect JavaScript/React files in `/frontend` or `/client`
- Parse `requirements.txt` and `package.json`
- Show both tech stacks in the presentation

## Example Project Structure

Here's what HackLuminary expects to find:

```
your-project/
├── README.md              # Title, description, features
├── src/                   # Source code
│   ├── main.py
│   ├── utils.py
│   └── ...
├── requirements.txt       # Python dependencies
└── package.json          # JavaScript dependencies (optional)
```

## Sample README Format

To get the best results, structure your README like this:

```markdown
# Project Name

Brief project description.

## Problem

What problem does your project solve?

## Solution

How does your project solve it?

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

Instructions here...

## Usage

Example usage here...
```

## Generated Presentation Structure

HackLuminary generates a presentation with these slides:

1. **Title**: Project name and description
2. **Problem**: The challenge you're addressing
3. **Solution**: Your approach to solving it
4. **Features**: Key capabilities (from README or auto-generated)
5. **Impact**: Benefits and value proposition
6. **Tech Stack**: Languages, frameworks, dependencies
7. **Future**: Roadmap and next steps
8. **Closing**: Thank you slide

## Tips for Best Results

### 1. Write a Good README

The better your README, the better your presentation:

- Clear problem statement
- Detailed solution description
- Bullet-pointed features
- Real-world examples

### 2. Organize Your Code

- Use standard directory structures
- Name entry points clearly (`main.py`, `index.js`, `app.py`)
- Keep dependency files up-to-date

### 3. Add Documentation

Include additional docs for deeper technical content:

- `ARCHITECTURE.md` for system design
- `TECHNICAL.md` for implementation details
- `DESIGN.md` for UX/UI decisions

### 4. Test Locally First

Always generate and review the presentation before demo day:

```bash
hackluminary --project-dir . --output test.html
open test.html  # Review in browser
```

## Real-World Example

Here's how we generated a presentation for TaskMaster Pro:

```bash
# Project structure
taskmaster-pro/
├── README.md           # Problem, solution, features
├── package.json        # React, Express, MongoDB
├── index.js            # Express server
└── TaskManager.js      # Core logic

# Generate presentation
hackluminary --project-dir taskmaster-pro --output demo.html

# Result
✅ Beautiful 8-slide presentation ready for demo day!
```

The generated presentation automatically included:

- Project name and description from README
- Problem statement from README
- Solution approach from README
- Features list from README
- Tech stack: JavaScript, React, Express, MongoDB
- Impact and future plans (auto-generated)

## Troubleshooting Examples

### Problem: No code detected

```bash
$ hackluminary --project-dir empty-folder
❌ Error: Failed to analyze codebase - no recognizable code found
```

**Solution**: Make sure your project has source code files with supported extensions.

### Problem: README not found

If you don't have a README, HackLuminary will:

- Use the directory name as the project title
- Auto-generate generic problem/solution statements
- List detected features from code structure

**Better solution**: Add a README.md with proper sections!

## Advanced Usage

### Generate for Multiple Projects

Create presentations for your whole team:

```bash
for dir in project1 project2 project3; do
  hackluminary --project-dir "$dir" --output "${dir}-presentation.html"
done
```

### Integrate with CI/CD

Generate presentations automatically on release:

```yaml
# .github/workflows/presentation.yml
name: Generate Presentation
on:
  release:
    types: [created]
jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install hackluminary
      - run: hackluminary --project-dir . --output presentation.html
      - uses: actions/upload-artifact@v2
        with:
          name: presentation
          path: presentation.html
```

## Next Steps

1. Try generating a presentation for your project
2. Review and refine your README if needed
3. Share the HTML with your team or judges
4. Open the file in any browser - no server needed!

For more information, see the main [README.md](README.md).
