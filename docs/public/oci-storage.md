# OCI Storage

## Retention strategy

- objects live under `aictx-runs/<run-id>/input|output|logs`
- cleanup is explicit and dry-run by default
- stale cleanup uses age filters; targeted cleanup uses run-id filters

## Artifact lifecycle

1. create deterministic snapshot
2. upload snapshot to `input/`
3. run OCI job/worker
4. upload `aictx-result.zip` to `output/`
5. retrieve logs/results explicitly
6. remove stale artifacts explicitly

## Cost expectations

- storage cost scales with snapshot/result size
- compute cost scales with runtime cap
- token estimate is included in `oci estimate`
- default warning threshold is $5 estimated cost

## Cleanup behavior

- `aictx clean --oci` previews deletes
- `aictx clean --oci --yes` applies deletes
- `--run-id` scopes to one run
- `--max-age-days` scopes stale cleanup

## Snapshot safety model

- excludes ignored/generated/binary/cache/git/runtime artifacts
- blocks forbidden secret-prone paths by default
- secret scans before packaging unless explicitly skipped
- verifies manifest, hashes, archive integrity, and forbidden paths before use

## Failure recovery

- bounded upload/download retries
- bundle verification before unpack
- explicit object-name download supports retrieval resume
- patch-first local review remains mandatory