# 0052 Step 2 — Python compatibility of regression test (23 November 2026)

The first retry after starting `development-infrastructure` failed during the offline
unit test `test_development_sql_uses_infrastructure_container`, before the apply
utility was invoked. The test used `mocked.call_args.args[0]`, which is not
portable to the user's Python/unittest.mock implementation: it evaluated to
`'args'` instead of the command argument list.

Change only the test to use the stable tuple-style access
`mocked.call_args[0][0]`. This preserves the original assertion that development
SQL targets `docker exec -i diaries-development-db`. No application utility, SQL,
image, production/development configuration or previously collected evidence is
changed. The prior failed run did not reach `--apply`.
