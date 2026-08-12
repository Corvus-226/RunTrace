# RunTrace

RunTrace is a lightweight CLI for capturing and comparing the code,
configuration, environment, and metadata behind machine-learning experiments.

> Project status: early development. `runtrace init` is available; the first
> complete experiment workflow is planned as v0.1.0.

The project and CLI are named RunTrace. The planned PyPI distribution name is
`ml-runtrace` because the `runtrace` distribution is already owned by an
unrelated project.

## Why RunTrace?

It is easy to end up with experiment folders such as `final`, `final-2`, and
`final-really`, then lose track of the Git commit, configuration, Python
environment, or command that produced a result. RunTrace is being built to
record that reproducibility context in transparent local files.

RunTrace is not intended to replace full experiment-tracking platforms such as
MLflow or Weights & Biases. Its focus is deliberately smaller:

- local-first and server-free;
- lightweight command-line workflows;
- human-readable snapshot files;
- Git-aware reproducibility metadata;
- no automatic upload of experiment data.

## Planned v0.1 workflow

```console
runtrace init
runtrace snapshot --name baseline --config configs/train.yaml \
  --command "python train.py --config configs/train.yaml"
runtrace list
runtrace show <run-id>
runtrace diff <run-id-a> <run-id-b>
```

`runtrace init` is implemented. The remaining commands are the v0.1.0 target
and will be delivered incrementally. See the repository issues for current
implementation status.

## Development setup

RunTrace requires Python 3.10 or newer. The project uses
[uv](https://docs.astral.sh/uv/) for its reproducible development environment.

```console
git clone https://github.com/Corvus-226/RunTrace.git
cd RunTrace
uv sync --all-groups
uv run runtrace --help
uv run pytest
```

The current skeleton also exposes its development version:

```console
uv run runtrace --version
```

## Privacy

RunTrace is local-only by default. It does not upload experiment data, source
code, credentials, or environment variables. Snapshot capture will be designed
to avoid collecting secrets.

## Contributing

The project is at an early stage and welcomes focused bug reports, design
feedback, and contributions. Read [CONTRIBUTING.md](CONTRIBUTING.md) before
opening a pull request.

## License

RunTrace is released under the [MIT License](LICENSE).
