# Frontend Lint Baseline

The frontend lint gate is active, but the current codebase still has a managed warning baseline.

Current ceiling:

- `npm run lint` allows at most 60 warnings.
- Any new warning above that ceiling fails the frontend quality gate.
- The target state is zero warnings or a much smaller set of intentional, line-level exceptions.

## Warning Groups

| Group | Current impact | Resolution path |
| --- | ---: | --- |
| React effect state updates | Most warnings | Move derived loading/reset state into event handlers, reducers, or request helpers where it makes the flow clearer. |
| Fast refresh export structure | Several warnings | Split non-component utilities from component/provider files. |
| Unused values/imports | Small number | Remove dead variables or wire them into the displayed UI when they represent intended metrics. |
| Redundant Boolean call | One warning | Replace the redundant conversion with the underlying condition. |

## Operating Rule

When a warning is fixed, lower the `--max-warnings` ceiling in `frontend/package.json` in the same change. This keeps quality moving in one direction.
