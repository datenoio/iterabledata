# Pipeline examples

Process data in a pipeline: read from a source iterable, transform each row with a function, optionally write to a destination iterable.

## Scripts

- **run_pipeline.py** – Run a pipeline with a process function (e.g. add a field, filter).

## Run

```bash
python examples/pipeline/run_pipeline.py [source.csv] [output.csv]
```

If files are omitted, the script uses minimal in-memory data for demonstration.

## API

```python
from iterable.helpers.detect import open_iterable
from iterable.pipeline.core import pipeline

def process(row, state):
    row["doubled"] = row.get("value", 0) * 2
    return row

with open_iterable("in.csv") as src, open_iterable("out.csv", mode="w", iterableargs={"keys": ["id", "value", "doubled"]}) as dst:
    result = pipeline(src, dst, process_func=process)
    print(result.rows_read, result.rows_written)
```
