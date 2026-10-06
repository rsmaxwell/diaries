# Step 12 standard client test run

After applying the Step 12 drop-in to the normal Diaries working tree, run from `diaries-client`:

```text
npm ci
npm test -- --watch=false --browsers=ChromeHeadless
```

If the project normally uses an already-restored `node_modules`, the `npm ci` step can be omitted.

Expected Step 12 outcome:

- all existing client tests remain green;
- the three new Step 12 spec files are discovered;
- no production source change is required to make the new tests pass.

Record the command output under `change-control/in-progress/0027-FEAT - add ImageFragment editing to diaries-client/evidence/Step 12/` before declaring the Step 12 standard-suite acceptance criterion complete.
