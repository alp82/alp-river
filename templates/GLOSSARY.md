# Glossary

Canonical terms for this project. Agents read this to avoid renaming the same concept three different ways across files.

## Terms

For each domain term, give the definition and the aliases to avoid. Aliases should be the names that have crept in elsewhere or that are tempting but wrong here.

### _TODO: Term_

**Definition:** _TODO:_ one to three sentences. Be precise about what it is and isn't.

**Avoid:** _TODO:_ alias1, alias2, alias3 (and why these are confusing - one line)

### _TODO: Term_

**Definition:** _TODO:_

**Avoid:** _TODO:_

## Relationships

_TODO:_ How the terms above connect. Useful when two concepts are easy to conflate. Short ASCII diagrams or one-line statements both work.

- _TODO:_ A contains many B (not the other way around)
- _TODO:_ C is the read-side projection of D - never write to C directly

## Flagged ambiguities

_TODO:_ Terms that genuinely don't have a settled definition yet, or that mean different things in different parts of the codebase. List them so agents know to ask before assuming.

- _TODO:_ "session" - means HTTP session in `auth/`, but means user-tracking session in `analytics/`. Plan to rename one.
- _TODO:_ ...
