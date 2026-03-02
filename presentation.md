---
marp: true
theme: default
paginate: true
---

---

# DocGenie

Auto-documentation tool that generates `README.md` and HTML docs for a codebase.

Claims:
- Auto-documentation tool that generates `README.md` and HTML docs for a codebase.

Evidence: doc.title, doc.description

---

## The Problem

- Teams lose demo time because project context is scattered across code, docs, and commits.
- The goal is to turn repository evidence into a concise story quickly.

Visuals:
![Bug icon software](C:\Users\Vladislav Kondratyev\.local\share\hackluminary\image_cache\158484398655ec99.png)
_Bug icon software_

Claims:
- Teams lose demo time because project context is scattered across code, docs, and commits.
- The goal is to turn repository evidence into a concise story quickly.

Evidence: doc.description, repo.project

---

## Our Solution

DocGenie consists of several key components:

- **CodebaseAnalyzer**: Multi-language code analysis engine with caching and concurrency
- **ParserRegistry**: Pluggable parsers (AST, tree-sitter, regex fallback) per language
- **ReadmeGenerator**: Jinja2-based template rendering system for markdown
- **HTMLGenerator**: Beautiful HTML documentation generator with responsive design
- **CLI Interface**: Typer + Rich powered user experience

Visuals:
![Python programming language](C:\Users\Vladislav Kondratyev\.local\share\hackluminary\image_cache\da153dc6e7ded43a.png)
_Python programming language_

Claims:
- DocGenie consists of several key components:

- **CodebaseAnalyzer**: Multi-language code analysis engine with caching and concurrency
- **ParserRegistry**: Pluggable parsers (AST, tree-sitter, regex fallback) per language
- **ReadmeGenerator**: Jinja2-based template rendering system for markdown
- **HTMLGenerator**: Beautiful HTML documentation generator with responsive design
- **CLI Interface**: Typer + Rich powered user experience

Evidence: doc.solution, repo.languages, repo.project

---

## Key Features

- Deterministic parsing of project source and documentation
- Branch-aware context from local git history
- Offline-first rendering with no runtime CDN dependencies
- JSON schema output suitable for automation

Visuals:
![DocGenie](C:\Users\Vladislav Kondratyev\.local\share\hackluminary\image_cache\ba6a2da75d51b5bd.png)
_DocGenie_

Claims:
- Deterministic parsing of project source and documentation
- Branch-aware context from local git history
- Offline-first rendering with no runtime CDN dependencies
- JSON schema output suitable for automation

Evidence: repo.features, repo.dependencies, repo.project

---

## Technology Stack

- Primary language: Python
- Language distribution: Python (45), JavaScript (37), HTML (22), CSS (4)
- Dependencies: click, typer, rich, structlog, tree-sitter-language-pack, gitpython, jinja2, pyyaml
- Scale: 108 source files, 51,143 lines

Visuals:
![Python programming language](C:\Users\Vladislav Kondratyev\.local\share\hackluminary\image_cache\da153dc6e7ded43a.png)
_Python programming language_

Claims:
- Primary language: Python
- Language distribution: Python (45), JavaScript (37), HTML (22), CSS (4)
- Dependencies: click, typer, rich, structlog, tree-sitter-language-pack, gitpython, jinja2, pyyaml
- Scale: 108 source files, 51,143 lines

Evidence: repo.languages, repo.dependencies, repo.files, repo.lines

---

## Impact & Benefits

- Cuts presentation prep time from hours to minutes
- Improves narrative consistency across team members
- Keeps technical claims traceable to repository evidence
- Works reliably in low-connectivity hackathon environments

Visuals:
![Bar chart statistics](C:\Users\Vladislav Kondratyev\.local\share\hackluminary\image_cache\1fc5fcbc334fe91c.png)
_Bar chart statistics_

Claims:
- Cuts presentation prep time from hours to minutes
- Improves narrative consistency across team members
- Keeps technical claims traceable to repository evidence
- Works reliably in low-connectivity hackathon environments

Evidence: doc.description, repo.files, repo.lines

---

# Thank You

DocGenie · Built with Python

Claims:
- DocGenie · Built with Python

Evidence: repo.languages, doc.title, repo.files, repo.lines
