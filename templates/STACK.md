# Stack

Not a dependency list. A statement of which tools the project uses at each layer, what constraints they impose, and why they were chosen. Agents read this to avoid suggesting the wrong library or pattern.

Group by layer. Each entry: tool name, the constraint it puts on the codebase, and a one-line why.

## Language and runtime

_TODO:_ e.g. TypeScript on Node 20+
- **Constraint:** _TODO:_ what this forces (strict mode, ESM-only, no top-level await before X, ...)
- **Why:** _TODO:_ one line

## Framework

_TODO:_ e.g. Next.js 15 (app router)
- **Constraint:** _TODO:_ server components by default, route handlers for APIs, no pages router
- **Why:** _TODO:_ one line

## Data layer

_TODO:_ e.g. Postgres via Prisma
- **Constraint:** _TODO:_ schema-first migrations, no raw SQL outside designated files
- **Why:** _TODO:_ one line

## Auth

_TODO:_ e.g. session cookies via lucia-auth
- **Constraint:** _TODO:_ ...
- **Why:** _TODO:_ ...

## UI / styling

_TODO:_ e.g. Tailwind v4 + shadcn/ui
- **Constraint:** _TODO:_ no CSS modules, design tokens via Tailwind theme
- **Why:** _TODO:_ one line

## Testing

_TODO:_ e.g. Vitest + Playwright
- **Constraint:** _TODO:_ unit tests colocated, e2e under `tests/e2e/`
- **Why:** _TODO:_ one line

## Tooling

_TODO:_ e.g. Biome for lint+format, pnpm for packages
- **Constraint:** _TODO:_ no Prettier, no ESLint, no npm/yarn lockfiles
- **Why:** _TODO:_ one line

## Hosting / deploy

_TODO:_ e.g. Vercel
- **Constraint:** _TODO:_ edge runtime for matching routes, no long-running processes
- **Why:** _TODO:_ one line

## Add or remove layers as needed
