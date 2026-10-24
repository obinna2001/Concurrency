# Concurrency

Export MySQL rows to CSV using sequential or concurrent processing.

Install dependencies with Python 3.13 or newer:

```bash
uv sync
```

Set the MySQL connection values in `src/concurrency/config/config.yaml` under
`env.database_config`. Set `env.global_config.batch_size` to the number of rows
to fetch per batch. The project root is determined automatically.

Run an export:

```bash
uv run concurrency concurrent
uv run concurrency sequential
```

Omitting the mode selects concurrent processing. Both modes are also available
through the module entry point:

```bash
uv run python -m concurrency sequential
```

Use `uv run concurrency --help` to see the available modes.

Sequential exports write to `data/transaction.csv`. Concurrent exports write
batch CSV files into a new directory under `data/`. Output directories are
created automatically.

Run the execution tests without connecting to MySQL:

```bash
uv run python -m unittest discover -s tests
```
