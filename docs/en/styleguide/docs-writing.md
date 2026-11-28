# Documentation and External Writing Guidelines

This page specifies the writing style and external (README/release page) writing guidelines for ErisPulse. The target audience is documentation contributors and those maintaining the README.

## 1. Document Writing

### 1. Value First

The first screen of every document should answer one question: "What will I gain from reading this?" Reference-style documents (consulted as needed) should begin with a unified `> [!TIP]` trigger description — **"When you need to read this: ... otherwise skip it"**; core must-read documents should use `> [!NOTE]` to indicate their position in the reading path.

### 2. Examples Over Narration

If something can be explained with a runnable code block, don't write descriptive paragraphs. Code examples must be directly copy-paste runnable (including imports and minimal context), and must not use `...` to omit key steps.

### 3. Trigger Descriptions as Retrieval Entry Points

The "when to read" sentence at the beginning of a document serves as matching text for AI assistants and search — write concrete scenarios ("When your adapter needs..."), not abstract categorizations ("This document introduces...").

### 4. Group Endings by Intent

"Next steps" links at the end of a document should be grouped by reader intent (want to dive deeper into X → Link A; encountering problem Y → Link B), not presented as an undifferentiated flat listing of the table of contents.

### 5. Changelog Writing

Changelogs record the net differences between release states, not the development process: multiple modifications to the same topic should update the existing entry to its final state; issues introduced and fixed within the same release cycle are not listed separately; internal adjustments imperceptible to users are not recorded. For the complete specification, see the "Writing Guidelines" at the top of `CHANGELOG.md`.

### 6. Version Annotation Guidelines

Version annotations in document bodies should only describe **behavioral differences**, not entry requirements:

- **Annotate behavioral differences in the body**: Only annotate when behavior changes across versions, and clearly state "what the difference is" — for example, "Since X.Y.Z, `reload()` performs a full reload by default (previously it only reloaded changed modules)". Readers use this to determine whether their code behaves differently under new versus old versions
- **Centralize "this feature requires X+"-style entry annotations in the version quick reference table**: Don't scatter them across document bodies; consolidate them in the version quick reference table in `docs/en/README.md`, and simply link there from the body when needed
- **Use placeholders for version numbers in examples**: Version numbers appearing in example code should use placeholder forms such as `x.y.z` to avoid becoming outdated with frequent releases (except for behavioral differences annotated with real version numbers in the body)

## 2. Public-Facing Pages (README / Release Pages)

### 1. Three-Part Structure

1. **Value Proposition**: A single sentence that makes clear "what you can do with it", immediately followed by a verifiable 30-second result (minimal example / demo video / screenshot)
2. **Proof**: Feature cards, real running screenshots, ecosystem scale—evidence ordered by persuasiveness, not piled up
3. **Call to Action**: Installation command copyable in one line; a clear next-step link for each major path (quick start / in-depth development / ecosystem exploration)

### 2. Scenario-Based Rather Than a Mere List

Every item in the feature list answers "what problem it solves", not "what we have". Each ecosystem showcase entry comes with a one-sentence applicable scenario and a minimal example—don't just paste a logo and call it done.

### 3. Language and Messaging

- **Primary Language**: Current state—Chinese (zh-CN) is the primary documentation source, with English and all other languages automatically generated from zh-CN by the CI translation pipeline (only modify `docs/zh-CN`; other languages sync via CI); goal—evolve toward English as the primary version over the long term. Until that goal is reached, public-facing pages are maintained under the "Chinese primary source, multilingual translated artifacts" model, and other languages are not labeled "pending sync" (CI guarantees automatic synchronization)
- Do not use internal jargon (module codenames, milestone names, internal process terms) on public-facing pages—readers are seeing the project for the first time
- Numbers and promises (versions, performance, support scope) must be consistent with the main documentation; outdated content is better deleted than kept

### 4. Conversion Structure of Quick Start Pages

`quick-start`-type pages: first deliver the "60-second win" (install → three lines of code → running result), then expand into explanations; users are willing to keep reading only after they have seen success.