# Cursor Skills

This directory contains Cursor Skills - reusable instructions that teach the AI assistant how to perform specific tasks automatically.

## What are Skills?

Skills are markdown files that extend the AI's capabilities for this project. Unlike commands (in `.cursor/commands/`), skills are automatically applied by the AI when relevant to the conversation.

## Directory Structure

Each skill is stored in its own directory:

```
.cursor/skills/
├── skill-name/
│   ├── SKILL.md              # Required - main instructions
│   ├── reference.md          # Optional - detailed documentation
│   └── examples.md           # Optional - usage examples
```

## Available Skills

- **iterabledata-development** - Core development workflows, patterns, and conventions
- **openspec-workflows** - OpenSpec proposal and implementation workflows
- **format-implementation** - Guide for implementing new data formats
- **testing-patterns** - Testing conventions and best practices
- **database-engine-implementation** - Guide for implementing database engines
- **ai-integration** - AI/LLM features, catalog, and agent patterns

A portable **usage** skill for *other* repositories (not loaded here) lives at [`skills/iterabledata/SKILL.md`](../../skills/iterabledata/SKILL.md). Copy it into a consumer project so coding agents generate `from iterable import open_iterable`.

## Creating New Skills

1. Create a new directory: `.cursor/skills/your-skill-name/`
2. Create `SKILL.md` with YAML frontmatter:
   ```markdown
   ---
   name: your-skill-name
   description: Brief description of what this skill does and when to use it
   ---
   ```
3. Write concise instructions (under 500 lines)
4. Use progressive disclosure - put detailed info in separate files

See the [Cursor Skills documentation](https://cursor.sh/docs/skills) for more details.

## Skills vs Commands

- **Skills** (`.cursor/skills/`) - Automatically applied by AI when relevant
- **Commands** (`.cursor/commands/`) - User-invoked shortcuts via Cursor command palette
