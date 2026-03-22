# E3-UI — Master Routing File

## Identity
E3-UI is an AI-powered email marketing platform with a FastAPI backend, vanilla JS frontend, and LangChain-based AI agents. It supports contact management, email design, campaign sending (via Mailgun), email validation (via NeverBounce), and AI-driven natural language queries against a CRM database. Authentication is handled via AWS Cognito and Google OAuth.


## Folder Structure

```text
e3-ui/
├── AGENTS.md
├── CONTEXT.md
├── agents/
│   ├── NaturalLanguageContactsValidator/
│   │   └── prompts/
│   ├── NaturalLanguageDatabase/
│   │   └── prompts/
│   ├── NaturalLanguageEmailDesigner/
│   │   └── prompts/
│   ├── NaturalLanguageEmailer_Mailgun/
│   │   └── prompts/
│   ├── NaturalLanguageHtmlSnippetEditor/
│   │   └── prompts/
│   ├── evaluators/
│   │   ├── prompts/
│   │   └── errors/
│   ├── guardrails/
│   ├── router/
│   └── prompts/
```

## Routing



| Task | Go to | Read |
|------|-------|------|
| Route NL queries to sub-agents | `agents/router/` | CONTEXT.md |
| Validate contacts via NeverBounce | `agents/NaturalLanguageContactsValidator/` | CONTEXT.md |
| Query contacts (NL → SQL) | `agents/NaturalLanguageDatabase/` | CONTEXT.md |
| Generate full HTML email designs | `agents/NaturalLanguageEmailDesigner/` | CONTEXT.md |
| Send campaigns / view metrics (Mailgun) | `agents/NaturalLanguageEmailer_Mailgun/` | CONTEXT.md |
| Edit HTML email snippets | `agents/NaturalLanguageHtmlSnippetEditor/` | CONTEXT.md |
| Agent output evaluation / error tracking | `agents/evaluators/` | CONTEXT.md |
| Input/output safety guardrails | `agents/guardrails/` | CONTEXT.md |
| View or edit project config | `agents/_config/` | CONTEXT.md |
| Project logs for all agent actions, thinking, and rationale | `agents/logs/` | CONTEXT.md |

## Naming Conventions
- None

## Rules
- Read this file first on every new task
- Each stage has its own `CONTEXT.md` — read it before working in that stage
- Do not create files outside of the defined structure without asking
- Keep `shared/` for cross-stage assets only
- When unsure which stage a task belongs to, ask
