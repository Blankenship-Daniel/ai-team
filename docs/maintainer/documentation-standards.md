# Documentation Standards

## File Organization

### Directory Structure
```
docs/
├── README.md                    # Documentation index (required)
├── user-guide/                 # End-user documentation
│   ├── getting-started.md      # Primary user entry point
│   └── advanced-usage.md       # Detailed configuration/usage
├── developer/                  # Technical implementation docs
│   ├── CLAUDE.md              # AI integration technical details
│   └── LEARNINGS.md           # Development insights
├── maintainer/                # Project maintenance docs
│   ├── documentation-standards.md  # This file
│   └── troubleshooting.md     # Common issues and solutions
└── archive/                   # Historical documents (read-only)
```

## Naming Conventions

### File Names
- Use lowercase with hyphens: `getting-started.md`, `api-reference.md`
- Be descriptive and specific: `installation.md` not `setup.md`
- Use `.md` extension for all documentation

### Headers
- Use sentence case: "Getting started" not "Getting Started"
- H1 for document title, H2 for major sections
- No more than 4 header levels deep

## Content Standards

### Structure
1. **Title** (H1) - Clear, actionable
2. **Brief description** - One sentence explaining purpose
3. **Main content** - Organized with clear H2 sections
4. **Cross-references** - Link to related docs at bottom

### Writing Style
- Write for the intended audience (user vs developer vs maintainer)
- Use active voice and imperative mood for instructions
- Include code examples with proper syntax highlighting
- Keep sentences concise and scannable

## Maintenance Rules

### File Ownership
- Each documentation file must have a clear owner/maintainer
- Update dates should be tracked in git history, not file metadata
- Broken or outdated docs are worse than no docs

### Update Process
1. **Never** create temporary documentation files in project root
2. **Always** update the docs index when adding new files
3. **Archive** outdated content rather than deleting it
4. **Review** documentation as part of feature development

### Anti-Patterns to Avoid
- Multiple README files with overlapping content
- "Update" or "Notes" files that never get cleaned up
- Documentation scattered in project root
- Duplicate installation instructions across multiple files

## Quality Checklist

Before committing documentation:
- [ ] File follows naming conventions
- [ ] Content is in appropriate directory for target audience
- [ ] docs/README.md index is updated
- [ ] Links to related documentation are included
- [ ] No redundant content exists elsewhere
- [ ] Tested all code examples and commands

---

*These standards prevent documentation entropy and ensure long-term maintainability.*