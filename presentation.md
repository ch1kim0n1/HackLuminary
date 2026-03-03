---
marp: true
theme: default
paginate: true
---

---

# HackLuminary v2.2

Offline-first, branch-aware presentation system with a NotebookLM-style local Studio and production deck renderer.

Claims:
- Offline-first, branch-aware presentation system with a NotebookLM-style local Studio and production deck renderer.

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

This workflow produces deterministic slides from repository facts and optional local AI refinement, keeping outputs reproducible while adapting narrative quality for Python projects.

Visuals:
![Python programming language](C:\Users\Vladislav Kondratyev\.local\share\hackluminary\image_cache\da153dc6e7ded43a.png)
_Python programming language_

Claims:
- This workflow produces deterministic slides from repository facts and optional local AI refinement, keeping outputs reproducible while adapting narrative quality for Python projects.

Evidence: repo.languages, repo.project

---

## Key Features

- Hybrid workflow: `studio` for drafting + `generate` for exports
- Source-grounded citations with snippet/line provenance
- Evidence explorer with search/filter/sort and per-slide evidence pinning
- Self-contained offline HTML deck output
- Presenter mode with notes, timer, progress timeline, jump controls
- Slide outline + reorder controls with keyboard shortcuts
- One-click Studio quality fixes (`Fix This`, `Fix All`) for common quality errors

Visuals:
![Command line interface terminal](C:\Users\Vladislav Kondratyev\.local\share\hackluminary\image_cache\8a3b4754a512b412.png)
_Command line interface terminal_

Claims:
- Hybrid workflow: `studio` for drafting + `generate` for exports
- Source-grounded citations with snippet/line provenance
- Evidence explorer with search/filter/sort and per-slide evidence pinning
- Self-contained offline HTML deck output
- Presenter mode with notes, timer, progress timeline, jump controls
- Slide outline + reorder controls with keyboard shortcuts
- One-click Studio quality fixes (`Fix This`, `Fix All`) for common quality errors

Evidence: doc.features, repo.dependencies, repo.project

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

## Technology Stack

- Primary language: Python
- Language distribution: Python (52), CSS (2), JavaScript (2), PowerShell (2), HTML (1)
- Dependencies: click, tomli
- Scale: 60 source files, 11,433 lines

Visuals:
![Python programming language](C:\Users\Vladislav Kondratyev\.local\share\hackluminary\image_cache\da153dc6e7ded43a.png)
_Python programming language_

Claims:
- Primary language: Python
- Language distribution: Python (52), CSS (2), JavaScript (2), PowerShell (2), HTML (1)
- Dependencies: click, tomli
- Scale: 60 source files, 11,433 lines

Evidence: repo.languages, repo.dependencies, repo.files, repo.lines

---

## Future Plans

- Add richer repository analysis for architecture-level insights
- Expand local model catalog and speed profiles for laptops
- Improve quality gates with domain-specific heuristics
- Ship stronger team templates for common hackathon judging tracks

Visuals:
![Road sign direction](C:\Users\Vladislav Kondratyev\.local\share\hackluminary\image_cache\b01fa1ef5f841e3a.jpg)
_Road sign direction_

Claims:
- Add richer repository analysis for architecture-level insights
- Expand local model catalog and speed profiles for laptops
- Improve quality gates with domain-specific heuristics
- Ship stronger team templates for common hackathon judging tracks

Evidence: repo.files

---

## Branch Delta

- Branch: ui-update
- Base branch: main
- 1 files changed (other:1).
- Top changed paths: scripts/git-switch-branch.ps1

Visuals:
![Git logo](C:\Users\Vladislav Kondratyev\.local\share\hackluminary\image_cache\650c1755912ee12c.png)
_Git logo_

Claims:
- Branch: ui-update
- Base branch: main
- 1 files changed (other:1).
- Top changed paths: scripts/git-switch-branch.ps1

Evidence: git.branch, git.base_branch, git.changed_files, git.change_summary

---

# Thank You

HackLuminary v2.2 · Built with Python

Claims:
- HackLuminary v2.2 · Built with Python

Evidence: repo.languages, doc.title, repo.files, repo.lines
