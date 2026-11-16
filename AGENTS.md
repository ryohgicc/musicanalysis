# Music Analysis

Reusable skill in `skills/music-analysis/`; scripts use Python standard library, browser report uses plain CSS/JS. Runtime has no Node dependency. Tests require Python 3.10+ and Playwright development tooling.

The released 声迹 v0.7.1 design is fixed: fullscreen scenes with immediate native-scroll response, overflow consumed before transitions, reading/reduced-motion fallback, and no bottom dock. The header includes local PNG screenshot export with an inline, hash-locked html2canvas asset and retained MIT license. Ordinary playlist generation changes data only; never edit template HTML, renderer, layout or the template lock for a new playlist. Preserve all main sections. Full reports must pass the content contract (9 chapters, 6 complete insights, 12 recommendations and bounded copy); missing data is only allowed in explicitly marked previews. Unknown chronology may use source-order content chapters but must never assert temporal evolution. Explicit design updates must update `assets/report-template.json` together with the template and pass the full gate.

Inspect `git status -sb` before edits. Keep generated private playlists, API responses, cookies, feedback and reports in ignored `work/`, `outputs/` or `.test-output/`. Development examples are fictional. The user explicitly authorized the real original report in `docs/index.html` and its user-requested motion variant in `docs/apple-motion-report/index.html` as public demos; this exception does not authorize publishing any other playlist. Preserve the original HTML unchanged unless the user requests its update; motion-demo changes stay in its separate directory; never overwrite it with the fictional example build. Do not reverse or silently trim playlist order. Do not invent listening chronology or audio features from metadata.

Commands from repository root:

- Install dev tools: `npm install`, `npx playwright install chromium`.
- Targeted data tests: `npm test`.
- Compile check: `npm run check`.
- Rebuild fictional example: `npm run build`.
- Browser checks: `npm run test:browser`.
- Public demo checks: `npm run test:demo`.
- Full gate: data tests, compile check, example build and browser checks above; include public demo checks when changing the demo or its deployment; run `npm run test:motion` for the motion demo and `npm run test:export` for the official screenshot feature. Rendering/template changes require browser checks; documentation-only edits need relevant reference/link review.

Update README when commands or user behavior change and CHANGELOG for released changes. Do not add personal fixture data, copied reference-site assets or upstream service implementations. Record new sources in `THIRD_PARTY_NOTICES.md` and keep the installed skill's `references/sources.md` consistent.

No database requirement. GitHub Pages serves the public demo from `main:/docs`; source pushes are automatically deployed by Pages. Keep the published commit on remote main. Before pushing fetch remote and check branch relationship; stage only task changes, never force-push unrelated work. Report commit, checks and live URL at handoff after deployment.
