# PromptWorks Frontend Internationalization

PromptWorks provides a collaborative workspace for managing prompt assets and model evaluations. This document explains how the web application now supports switching its interface between Simplified Chinese and English.

## Language Switching Overview

- The global language selector lives in the top-right corner of the console header.
- Chinese (`zh-CN`) remains the default experience for existing users.
- Selecting English (`en-US`) updates Element Plus widgets and all translated business copy.
- Preferences are persisted to `localStorage` so the chosen locale is restored on the next visit.

## Implementation Notes

- The frontend is built with Vue 3, Vite, and Element Plus.
- `vue-i18n` manages runtime locale state and message formatting.
- Each domain view keeps its translation strings close to the implementation to simplify maintenance.
- Shared labels (e.g., "Cancel", "Submit", "Not set") live in a common dictionary for reuse.

## Developer Workflow

```bash
cd frontend
npm install
npm run dev
```

While iterating on translations, run `npm run build` to ensure TypeScript types remain valid. Unit tests continue to execute with `uv run poe test-all` for the backend and `npm test` (future) for the frontend.

## Related Resources

- [Repository root README](../README.md)
- [Backend contribution guide](../TODO.md)

For a deeper dive into the product vision and architectural decisions, refer back to the primary README linked above.
