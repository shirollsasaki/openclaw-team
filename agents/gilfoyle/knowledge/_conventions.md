# Knowledge Graph Conventions

## Format
- Each file = one entity (person, project, org, topic, decision)
- Filename = entity name in kebab-case: `claw-deploy.md`, `lauki-antonson.md`
- Use [[Obsidian Backlinks]] to reference other entities: [[ClawDeploy]], [[Richard]]
- Each file starts with `# Entity Name` header
- Include `**Last Updated**: YYYY-MM-DD` after the header
- Max 2000 chars per entity file

## Sections
- **Summary**: 1-2 sentences — what is this entity
- **Status**: Current state (active/paused/archived)
- **Key Facts**: Bullet list of important information
- **Related**: [[Backlinks]] to connected entities
- **History**: Timestamped entries (most recent first)

## Reading Knowledge
- Before major tasks, read relevant files: `cat knowledge/my-focus.md`
- For shared product context: `cat $OPENCLAW_HOME/richard/knowledge/claw-deploy.md`

## Writing Knowledge
- Only write to YOUR OWN knowledge/ directory
- Only Richard writes to shared entities (claw-deploy.md, team.md, etc.)
- Append with timestamp: `## Update YYYY-MM-DD\n- Finding here`
- Keep files under 2000 chars — prune old History entries if needed
