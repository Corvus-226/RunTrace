"""Read and validate user-supplied experiment configuration files."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ConfigDict, JsonValue, TypeAdapter, ValidationError

_JSON_VALUE_ADAPTER = TypeAdapter(
    JsonValue,
    config=ConfigDict(strict=True, allow_inf_nan=False),
)


class ConfigLoadError(RuntimeError):
    """Raised when an experiment configuration cannot be captured safely."""


@dataclass(frozen=True, slots=True)
class LoadedConfig:
    """A portable config path, raw-content digest, and parsed JSON value."""

    path: str
    sha256: str
    values: JsonValue


def load_yaml_config(
    path: Path,
    *,
    current_directory: Path,
    project_root: Path,
) -> LoadedConfig:
    """Load a UTF-8 YAML config within ``project_root`` without unsafe tags."""
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = Path(current_directory) / candidate

    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as error:
        raise ConfigLoadError(f"Config file does not exist: {candidate}.") from error
    except OSError as error:
        raise ConfigLoadError(
            f"Could not resolve config file {candidate}: {error}"
        ) from error
    if not resolved.is_file():
        raise ConfigLoadError(f"Config path is not a file: {candidate}.")

    resolved_root = Path(project_root).resolve(strict=True)
    try:
        relative_path = resolved.relative_to(resolved_root)
    except ValueError as error:
        raise ConfigLoadError(
            f"Config file must be inside the Git repository: {candidate}."
        ) from error

    try:
        raw_config = resolved.read_bytes()
    except OSError as error:
        raise ConfigLoadError(
            f"Could not read config file {candidate}: {error}"
        ) from error
    try:
        config_text = raw_config.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ConfigLoadError(
            f"Config file must be UTF-8 encoded YAML: {relative_path.as_posix()}."
        ) from error

    try:
        parsed_config = yaml.safe_load(config_text)
    except yaml.YAMLError as error:
        raise ConfigLoadError(
            f"Config file contains invalid YAML: {relative_path.as_posix()}."
        ) from error

    try:
        validated_config = _JSON_VALUE_ADAPTER.validate_python(parsed_config)
    except (RecursionError, ValidationError) as error:
        raise ConfigLoadError(
            "Config values must use JSON-compatible YAML structures "
            f"(strings, numbers, booleans, null, lists, and string-keyed maps): "
            f"{relative_path.as_posix()}."
        ) from error

    return LoadedConfig(
        path=relative_path.as_posix(),
        sha256=hashlib.sha256(raw_config).hexdigest(),
        values=validated_config,
    )
