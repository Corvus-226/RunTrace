# Correlating RunTrace runs with logs and traces

This guide describes the run-ID correlation contract shipped in RunTrace
v0.3.0. The release is available from the versioned
[PyPI files](https://pypi.org/project/ml-runtrace/0.3.0/) and
[GitHub Release](https://github.com/Corvus-226/RunTrace/releases/tag/v0.3.0).

RunTrace records reproducibility context; observability systems record what an
application did while it was running. The shared value between those layers is
the RunTrace run ID.

## The child-process contract

When you use the snapshot-before-execution wrapper:

```console
ml-runtrace run --name baseline -- python train.py
```

RunTrace first saves `.runtrace/runs/<run-id>.yaml`. Only after that save
succeeds does it start the command with this additional environment variable:

```text
RUNTRACE_RUN_ID=<run-id>
```

The value is the same 12-character ID printed by the CLI, stored inside the
snapshot, and used in the YAML filename. RunTrace replaces a stale inherited
`RUNTRACE_RUN_ID` for the child but does not change the parent shell. Ordinary
descendants inherit the value unless the application deliberately replaces or
filters their environments.

Manual `ml-runtrace snapshot` does not launch a process, so it has no child
environment to modify.

## Put the ID in a structured log

No logging dependency is required. For example, an application can include the
ID in JSON output:

```python
import json
import os

run_id = os.environ.get("RUNTRACE_RUN_ID")
print(json.dumps({"event": "training_started", "runtrace.run.id": run_id}))
```

Instrumentation should omit the field when `RUNTRACE_RUN_ID` is absent so the
same program can still run outside the wrapper.

## Put the ID on an OpenTelemetry span

If the application already uses OpenTelemetry, it can attach the ID as a
custom span attribute without RunTrace depending on or configuring
OpenTelemetry:

```python
import os

from opentelemetry import trace

run_id = os.environ.get("RUNTRACE_RUN_ID")
if run_id is not None:
    trace.get_current_span().set_attribute("runtrace.run.id", run_id)
```

`runtrace.run.id` is a RunTrace-specific attribute, not an OpenTelemetry
semantic convention. Teams may apply the same value to a resource, root span,
metric label, or log field according to their existing instrumentation policy.
RunTrace deliberately does not rewrite `OTEL_RESOURCE_ATTRIBUTES`, create a
span, select an exporter, or send telemetry.

## Investigate an observed event

Copy the `runtrace.run.id` value from the log or trace, return to the relevant
Git repository, and inspect the local record:

```console
ml-runtrace show a31f82000001
```

That record identifies the Git state, config, Python runtime, installed
distributions, direct dependency origins, optional GPU metadata, and exact
wrapped command for the event.

## Process and privacy boundaries

- Local child processes normally inherit `RUNTRACE_RUN_ID`. Remote workers,
  containers, schedulers, and environment-sanitizing launchers require the
  application or orchestration layer to forward it explicitly.
- The run ID is not a credential, but it is a correlation identifier. Sending
  it to an observability backend can connect an external event to a local
  snapshot, so use the same access policy as the surrounding telemetry.
- RunTrace injects only its generated ID. It does not inspect, record, or upload
  other inherited environment-variable values.
- Attaching the ID to telemetry is opt-in application or instrumentation
  behavior. RunTrace remains local-first and has no network path.
