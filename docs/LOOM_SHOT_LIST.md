# Recording interactions — total target 4:30

1. 0:00 — Open README at repository top; show public links and assessment defaults.
2. 0:25 — Open the actual hosted homepage. Show provider and illustrative-price labels. Submit Chicago, IL → Dallas, TX in strict mode. Pan the real route, inspect one selected pin and its purchase.
3. 1:15 — Open Postman with the hosted environment from `SUBMISSION_LINKS.md`. Send request 1. Expand `fuel_stops`, `fuel_summary`, `cost_basis` and `meta`; read actual values.
4. 1:55 — Send short request 2. Show positive consumed gallons and zero purchases. Do not call its fuel cost zero.
5. 2:10 — Send repeat request 3. Show route/plan cache hit and zero directions calls. Send changed-fuel request 11 if time permits, showing geometry reuse.
6. 2:40 — In GitHub/editor show `api/views.py`, `api/service.py`, `routing/provider.py` and `optimizer/engine.py`. Highlight their responsibilities and next-cheaper decision. Show the independent oracle in `tests/test_optimizer.py`.
7. 3:30 — Show final test/CI/production Postman evidence in `FINAL_SUBMISSION_AUDIT.md`; state actual skips and provider status. Return to the UI, switch estimated mode, show conditional labels and the paired fuel timeline. If needed show Seattle’s useful gap response.
8. 4:15 — Return to README links and close. Stop by 4:30; review the recording and publish only if under five minutes and free of secret screens.

Prepare the service before recording to avoid free-host wake latency on camera. Do not clear a shared public cache or run provider load tests during the recording. A warm repeat is an honest demonstration; a cold one-call claim needs the separately captured cold evidence.
