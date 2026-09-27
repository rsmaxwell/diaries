# Step 15.4 / 15.5 close-out

The close-out material records the stable design and evidence already established by Steps 2–14. `finalise-step15.py` will only declare Step 15 complete after a clean `deployment/final-run/result.json` proves the remaining real-process deployment checks.

With `--apply-docs`, the finaliser also updates the feature-level `README.md` and `IMPLEMENTATION-STEPS-0025.md` **only after** all required result flags and cleanup checks pass. Before modification it writes complete before-closeout copies into `closeout/final-run`.

The finaliser marks the feature acceptance checklist complete, records 15.2–15.5 as completed, and keeps the production authoring restriction explicit. It does not move the feature directory or deploy/migrate production.
