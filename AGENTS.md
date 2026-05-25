<!-- SPECKIT START -->
Follow `.specify/memory/constitution.md` as the governing project rules.
For additional context about technologies to be used, project structure,
shell commands, and other important information for the active feature, read
`specs/003-skill-prerequisite-guidance/plan.md`.

Write project documentation, specs, plans, tasks, generated agent instructions,
runtime guidance, run requests, and skills in English.

Use pt-BR for chat with the project owner unless they ask otherwise.

ProofSignal Spec is the open interface layer over ProofSignal Core. Keep Core
interaction behind the documented public CLI JSON contract; do not import
private ProofSignal Core packages or read undocumented report internals.

Keep target-project state under `.proofsignal/`. Use cases reference exactly one
run request, while skills are decoupled reusable artifacts that may be shared by
multiple run requests.
<!-- SPECKIT END -->
