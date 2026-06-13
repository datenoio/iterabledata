from __future__ import annotations

import ast

# Try to import pandas for optimized DataFrame conversions
import importlib.util
import typing
import warnings

import duckdb

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import FormatNotSupportedError, FormatParseError, ReadError

HAS_PANDAS = importlib.util.find_spec("pandas") is not None

DUCKDB_CACHE_SIZE = 1000


class DuckDBEngineIterable(BaseFileIterable):
    def __init__(
        self,
        filename: str = None,
        stream: typing.IO = None,
        codec: BaseCodec = None,
        engine: str = "duckdb",
        mode: str = "r",
        encoding: str = "utf8",
        options: dict = None,
    ):
        if options is None:
            options = {}
        # The DuckDB engine reads from a file path; validate it up front so that
        # a missing/invalid filename surfaces as a typed ReadError rather than a
        # generic "no source" ValueError from the base class.
        if stream is None and codec is None:
            if filename is None:
                raise ReadError(
                    "DuckDB engine requires a filename",
                    filename=None,
                    error_code="INVALID_PARAMETER",
                )
            if not isinstance(filename, str):
                raise ReadError(
                    "Filename must be a string",
                    filename=None,
                    error_code="INVALID_PARAMETER",
                )
        self.pos = 0
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        self._connection = None
        self._current_batch = None
        self._batch_size = DUCKDB_CACHE_SIZE
        self._offset = 0  # Offset of the currently cached batch

        # Extract pushdown parameters from options
        self._columns = options.get("columns")
        self._filter = options.get("filter")
        self._query = options.get("query")

        # Track if callable filter was translated to SQL (for fallback handling)
        self._filter_translated = False

        # Validate parameters
        if self._query:
            # Validate query is read-only (no DDL/DML operations)
            # Validation can be done without a connection - just check the query string
            self._validate_query(self._query)
            if self._columns or self._filter:
                warnings.warn(
                    "When 'query' parameter is provided, 'columns' and 'filter' parameters are ignored.",
                    UserWarning,
                    stacklevel=2,
                )

        # Detect file format for appropriate DuckDB function
        self._file_format = self._detect_file_format()
        self._duckdb_function = self._get_duckdb_function()

    @staticmethod
    def id() -> str:
        return "duckdb"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def open(self):
        """No need to open iterable for DuckDB"""
        pass

    def close(self):
        """Close DuckDB connection and clean up resources"""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        self._current_batch = None
        self._offset = 0

    def _detect_file_format(self) -> str:
        """Detect file format from filename extension"""
        if not self.filename:
            return "csv"  # Default fallback

        filename_lower = self.filename.lower()

        # Handle compressed files - remove compression extension
        compression_extensions = (".gz", ".zst", ".zstd")
        if filename_lower.endswith(compression_extensions):
            # Remove compression extension
            base_name = filename_lower.rsplit(".", 1)[0]
        else:
            base_name = filename_lower

        # Detect format from extension (check in order of specificity)
        if base_name.endswith(".parquet"):
            return "parquet"
        elif base_name.endswith((".jsonl", ".ndjson")):
            return "jsonl"
        elif base_name.endswith(".json"):
            return "json"
        elif base_name.endswith(".csv"):
            return "csv"
        else:
            # Default to CSV for backward compatibility
            return "csv"

    def _get_duckdb_function(self) -> str:
        """Get the appropriate DuckDB function name for the file format"""
        format_to_function = {
            "csv": "read_csv_auto",
            "jsonl": "read_json_auto",
            "json": "read_json_auto",
            "parquet": "read_parquet",
        }
        return format_to_function.get(self._file_format, "read_csv_auto")

    def _escape_filename(self, filename: str) -> str:
        """Escape single quotes in filename to prevent SQL injection"""
        return filename.replace("'", "''")

    def _validate_query(self, query: str) -> None:
        """Validate that query is read-only (no DDL/DML operations)"""
        query_upper = query.upper().strip()

        # Check for DDL operations
        ddl_keywords = ["CREATE", "DROP", "ALTER", "TRUNCATE"]
        for keyword in ddl_keywords:
            if keyword in query_upper:
                raise ReadError(
                    f"Query contains DDL operation '{keyword}'. Only SELECT queries are allowed.",
                    filename=self.filename,
                    error_code="INVALID_QUERY",
                )

        # Check for DML operations
        dml_keywords = ["INSERT", "UPDATE", "DELETE", "MERGE"]
        for keyword in dml_keywords:
            if keyword in query_upper:
                raise ReadError(
                    f"Query contains DML operation '{keyword}'. Only SELECT queries are allowed.",
                    filename=self.filename,
                    error_code="INVALID_QUERY",
                )

        # Check that it starts with SELECT
        if not query_upper.startswith("SELECT"):
            raise ReadError(
                "Query must be a SELECT statement.",
                filename=self.filename,
                error_code="INVALID_QUERY",
            )

    def _translate_callable_filter(self, filter_func: typing.Callable) -> str | None:
        """Attempt to translate a Python callable filter to SQL WHERE clause"""
        # This is a simplified translator for common patterns
        # For complex callables, returns None to fall back to Python filtering

        try:
            # Get the source code of the function
            import inspect

            try:
                source = inspect.getsource(filter_func)
            except (OSError, TypeError):
                # Can't get source (might be a builtin or compiled function)
                return None

            # Parse the AST
            try:
                tree = ast.parse(source)
            except SyntaxError:
                return None

            # Extract the lambda or function body
            if not tree.body or not isinstance(tree.body[0], (ast.FunctionDef, ast.Lambda)):
                return None

            expr = tree.body[0]
            if isinstance(expr, ast.FunctionDef):
                if not expr.body or not isinstance(expr.body[0], ast.Return):
                    return None
                body = expr.body[0].value
            else:  # ast.Lambda
                body = expr.body

            # Translate the expression to SQL
            sql = self._translate_ast_to_sql(body)
            return sql

        except Exception:
            # If translation fails, fall back to Python filtering
            return None

    def _translate_ast_to_sql(self, node: ast.AST) -> str | None:
        """Translate an AST node to SQL WHERE clause"""
        if isinstance(node, ast.Compare):
            # Handle comparisons: row['col'] > value, row['col'] == value, etc.
            if len(node.ops) == 0 or len(node.comparators) != 1:
                return None

            left = node.left
            op = node.ops[0]
            right = node.comparators[0]

            # Extract column name from row['col'] pattern
            col_name = self._extract_column_name(left)
            if col_name is None:
                return None

            # Extract value
            value = self._extract_value(right)
            if value is None:
                return None

            # Translate operator
            op_map = {
                ast.Eq: "=",
                ast.NotEq: "!=",
                ast.Lt: "<",
                ast.LtE: "<=",
                ast.Gt: ">",
                ast.GtE: ">=",
                ast.In: "IN",
                ast.NotIn: "NOT IN",
            }
            sql_op = op_map.get(type(op))
            if sql_op is None:
                return None

            # Format SQL condition
            if isinstance(op, (ast.In, ast.NotIn)) and isinstance(value, list):
                # Handle IN/NOT IN with list
                value_str = "(" + ", ".join(self._format_sql_value(v) for v in value) + ")"
            else:
                value_str = self._format_sql_value(value)

            return f"{col_name} {sql_op} {value_str}"

        elif isinstance(node, ast.BoolOp):
            # Handle AND/OR operations
            op_map = {ast.And: "AND", ast.Or: "OR"}
            sql_op = op_map.get(type(node.op))
            if sql_op is None:
                return None

            # Translate each operand
            translated = []
            for value in node.values:
                sql_part = self._translate_ast_to_sql(value)
                if sql_part is None:
                    return None  # Can't translate one part, abort
                translated.append(f"({sql_part})")

            return f" {' ' + sql_op + ' '.join(translated)}"

        elif isinstance(node, ast.UnaryOp):
            # Handle NOT operations
            if isinstance(node.op, ast.Not):
                operand = self._translate_ast_to_sql(node.operand)
                if operand is None:
                    return None
                return f"NOT ({operand})"

        # For other patterns, return None to fall back to Python filtering
        return None

    def _extract_column_name(self, node: ast.AST) -> str | None:
        """Extract column name from row['col'] pattern"""
        if isinstance(node, ast.Subscript):
            # Handle row['col'] pattern
            if isinstance(node.value, ast.Name) and node.value.id in ("row", "x", "item"):
                if isinstance(node.slice, ast.Constant):
                    return str(node.slice.value)
                elif isinstance(node.slice, ast.Str):  # Python < 3.8
                    return node.slice.s
        elif isinstance(node, ast.Attribute):
            # Handle row.col pattern
            if isinstance(node.value, ast.Name) and node.value.id in ("row", "x", "item"):
                return node.attr
        elif isinstance(node, ast.Name):
            # Handle direct column name (if row is unpacked)
            return node.id
        return None

    def _extract_value(self, node: ast.AST) -> typing.Any:
        """Extract value from AST node"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Str):  # Python < 3.8
            return node.s
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.List):
            # Extract list values
            values = []
            for elt in node.elts:
                val = self._extract_value(elt)
                if val is None:
                    return None
                values.append(val)
            return values
        elif isinstance(node, ast.Tuple):
            # Extract tuple values
            values = []
            for elt in node.elts:
                val = self._extract_value(elt)
                if val is None:
                    return None
                values.append(val)
            return values
        return None

    def _format_sql_value(self, value: typing.Any) -> str:
        """Format a Python value as SQL literal"""
        if isinstance(value, str):
            # Escape single quotes and wrap in quotes
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(value, (int, float)):
            return str(value)
        elif value is None:
            return "NULL"
        else:
            # For other types, convert to string (may not be perfect)
            escaped = str(value).replace("'", "''")
            return f"'{escaped}'"

    def _validate_columns(self, columns: list[str]) -> None:
        """Validate that specified columns exist in the file"""
        if not columns:
            return

        self._ensure_connection()
        safe_filename = self._escape_filename(self.filename)

        # Get column names from the file by querying with LIMIT 0
        try:
            # Query to get column names (LIMIT 0 to avoid reading data)
            # Using parameterized query for consistency (LIMIT 0 is safe but follows pattern)
            test_query = f"SELECT * FROM {self._duckdb_function}('{safe_filename}') LIMIT ?"
            result = self._connection.execute(test_query, [0])
            available_columns = {desc[0].lower() for desc in result.description} if result.description else set()
        except (duckdb.Error, duckdb.ProgrammingError, duckdb.OperationalError):
            # If we can't get column info, skip validation (backward compatibility)
            # DuckDB will raise an error if column doesn't exist anyway
            # Log the specific DuckDB error but don't fail validation
            return
        except Exception:
            # For other unexpected errors, still skip validation but preserve error info
            # This maintains backward compatibility while allowing DuckDB to handle errors
            return

        # Check each requested column
        invalid_columns = []
        for col in columns:
            if col.lower() not in available_columns:
                invalid_columns.append(col)

        if invalid_columns:
            # Format error message with suggestions
            available_list = sorted(available_columns)
            error_msg = f"Invalid column name(s): {', '.join(invalid_columns)}"
            if available_list:
                error_msg += f". Available columns: {', '.join(available_list)}"
            raise FormatNotSupportedError(
                format_id=self._file_format,
                reason=error_msg,
            )

    def _build_sql_query(self, limit: int | None = None, offset: int | None = None) -> tuple[str, list]:
        """Build SQL query with pushdown optimizations using parameterized queries.

        Returns:
            tuple[str, list]: (query_string, parameters) where parameters is a list of values
            for the ? placeholders in the query string.
        """
        safe_filename = self._escape_filename(self.filename)
        parameters: list = []

        # If custom query is provided, use it directly (after validation)
        if self._query:
            self._validate_query(self._query)
            query = self._query
            # Users must reference files correctly in their query using read functions
            # Example: SELECT * FROM read_csv_auto('file.csv') WHERE col > 10
            # Add LIMIT and OFFSET if needed (only if not already present)
            if limit is not None and "LIMIT" not in query.upper():
                query += " LIMIT ?"
                parameters.append(limit)
            if offset is not None and "OFFSET" not in query.upper():
                query += " OFFSET ?"
                parameters.append(offset)
            return (query, parameters)

        # Validate columns if specified
        if self._columns:
            self._validate_columns(self._columns)
            columns_str = ", ".join(self._columns)
            select_clause = f"SELECT {columns_str}"
        else:
            select_clause = "SELECT *"

        # FROM: filename escaped, not parameterized (DuckDB read_* need string literals)
        from_clause = f"FROM {self._duckdb_function}('{safe_filename}')"

        # Build WHERE clause
        where_clause = ""
        self._filter_translated = False
        if self._filter:
            if isinstance(self._filter, str):
                # SQL string filter - use directly (user-provided SQL, already validated)
                where_clause = f"WHERE {self._filter}"
            elif callable(self._filter):
                # Python callable - try to translate
                # For callable filters, we always apply Python-side filtering as fallback
                # Translation to SQL is attempted but Python filtering is still applied
                sql_filter = self._translate_callable_filter(self._filter)
                if sql_filter:
                    where_clause = f"WHERE {sql_filter}"
                    self._filter_translated = True
                # If translation fails, filtering will be done in Python (handled in read methods)

        # Combine query parts
        query_parts = [select_clause, from_clause]
        if where_clause:
            query_parts.append(where_clause)

        query = " ".join(query_parts)

        # Add LIMIT and OFFSET using parameterized queries
        if limit is not None:
            query += " LIMIT ?"
            parameters.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            parameters.append(offset)

        return (query, parameters)

    def _ensure_connection(self):
        """Ensure DuckDB connection is established.

        Creates a connection lazily on first use and reuses it throughout
        the instance lifetime. Connection pooling is not implemented because:
        - DuckDB is an in-process database with lightweight connections
        - Each instance processes one file and reuses its connection efficiently
        - The typical usage pattern (sequential file processing) doesn't benefit from pooling
        - Adding pooling would add complexity without clear performance benefit
        """
        if self._connection is None:
            self._connection = duckdb.connect()
            # Validate filename is a string (not user input SQL)
            if not isinstance(self.filename, str):
                raise ReadError(
                    "Filename must be a string",
                    filename=None,
                    error_code="INVALID_PARAMETER",
                )
            # DuckDB's read functions handle file paths safely
            # The filename is validated and escaped before use

    def totals(self):
        """Returns total number of records"""
        self._ensure_connection()

        # If custom query is provided, we need to count from that query
        if self._query:
            self._validate_query(self._query)
            # Wrap query in a subquery to count (no parameters needed for COUNT)
            count_query = f"SELECT COUNT(*) FROM ({self._query})"
            try:
                result = self._connection.execute(count_query).fetchone()
                return result[0] if result else 0
            except Exception as e:
                raise FormatParseError(
                    format_id=self._file_format,
                    message=f"Failed to execute count query: {str(e)}",
                    filename=self.filename,
                ) from e

        # Build query with filter pushdown
        safe_filename = self._escape_filename(self.filename)

        # Build WHERE clause if filter is provided
        where_clause = ""
        if self._filter and isinstance(self._filter, str):
            where_clause = f"WHERE {self._filter}"

        # COUNT query doesn't need LIMIT/OFFSET, so no parameters needed
        count_query = f"SELECT COUNT(*) FROM {self._duckdb_function}('{safe_filename}')"
        if where_clause:
            count_query += f" {where_clause}"

        try:
            result = self._connection.execute(count_query).fetchone()
            count = result[0] if result else 0
        except Exception as e:
            raise FormatParseError(
                format_id=self._file_format,
                message=f"Failed to execute count query: {str(e)}",
                filename=self.filename,
            ) from e

        # If filter is a callable, we need to count in Python (fallback)
        if self._filter and callable(self._filter):
            # Count all rows and filter in Python
            all_query = f"SELECT * FROM {self._duckdb_function}('{safe_filename}')"
            try:
                result = self._connection.execute(all_query)
                all_dicts = self._result_to_dicts(result)
                count = sum(1 for row in all_dicts if self._filter(row))
            except Exception as e:
                raise FormatParseError(
                    format_id=self._file_format,
                    message=f"Failed to execute query for callable filter: {str(e)}",
                    filename=self.filename,
                ) from e

        return count

    def reset(self):
        """Resets counter and clears batch cache"""
        self.pos = 0
        self._offset = 0
        self._current_batch = None
        # Note: Connection is kept open for efficiency (can be reused)

    def _get_current_batch_index(self) -> int:
        """Get the batch index (which batch we're currently in)"""
        return self.pos // self._batch_size

    def _get_batch_offset(self, batch_index: int) -> int:
        """Get the offset for a given batch index"""
        return batch_index * self._batch_size

    @staticmethod
    def _stringify_value(value: typing.Any) -> typing.Any:
        """Coerce a value to ``str`` to match the text-format (CSV) contract.

        ``None``/NaN are preserved as ``None``.
        """
        if value is None:
            return None
        # Detect NaN without importing numpy/pandas (NaN != NaN).
        if isinstance(value, float) and value != value:
            return None
        return str(value)

    def _stringify_row(self, row: dict) -> dict:
        return {k: self._stringify_value(v) for k, v in row.items()}

    def _result_to_dicts(self, result) -> list[dict]:
        """Convert DuckDB result to list of dicts efficiently.

        Uses DuckDB's native DataFrame conversion if pandas is available,
        otherwise falls back to manual conversion.

        For text-based formats (CSV) all values are coerced to strings so that
        the DuckDB engine matches the contract of the internal CSV reader, where
        every field is a string.

        Args:
            result: DuckDB result object from execute()

        Returns:
            list[dict]: List of dictionaries, one per row
        """
        stringify = self._file_format == "csv"
        if HAS_PANDAS:
            # Use DuckDB's optimized DataFrame conversion
            try:
                df = result.df()
                # Convert DataFrame to list of dicts (faster than manual conversion)
                dicts = df.to_dict("records")

                # Handle column filtering if specified (more efficient with DataFrame)
                if self._columns:
                    # Filter columns before conversion if possible, otherwise filter after
                    if all(col in df.columns for col in self._columns):
                        df_filtered = df[self._columns]
                        dicts = df_filtered.to_dict("records")
                    else:
                        # Fallback: filter dicts after conversion
                        dicts = [{k: row.get(k) for k in self._columns if k in row} for row in dicts]

                if stringify:
                    dicts = [self._stringify_row(row) for row in dicts]
                return dicts
            except (duckdb.Error, duckdb.ProgrammingError, duckdb.OperationalError):
                # DuckDB-specific errors - fall back to manual conversion
                # This can happen if DataFrame conversion fails for some reason
                pass
            except Exception:
                # Other unexpected errors during DataFrame conversion - fall back to manual conversion
                pass

        # Fallback: manual conversion (used when pandas not available or conversion fails)
        rows = result.fetchall()
        columns = [desc[0] for desc in result.description] if result.description else []
        dicts = [dict(zip(columns, row, strict=False)) for row in rows]

        # Handle column filtering if specified
        if self._columns:
            dicts = [{k: row.get(k) for k in self._columns if k in row} for row in dicts]

        if stringify:
            dicts = [self._stringify_row(row) for row in dicts]
        return dicts

    def _load_batch(self, batch_index: int | None = None):
        """Load batch for the given batch index (or current position if None)"""
        self._ensure_connection()

        # Determine which batch to load
        if batch_index is None:
            batch_index = self._get_current_batch_index()

        batch_offset = self._get_batch_offset(batch_index)

        # Only reload if we need a different batch (simplified check - compare offsets directly)
        if self._offset != batch_offset or self._current_batch is None:
            # Build SQL query with pushdown optimizations (using parameterized queries)
            query, params = self._build_sql_query(limit=self._batch_size, offset=batch_offset)
            try:
                result = self._connection.execute(query, params)
            except Exception as e:
                # Convert DuckDB errors to our exception hierarchy
                raise FormatParseError(
                    format_id=self._file_format,
                    message=f"Failed to execute query: {str(e)}",
                    filename=self.filename,
                ) from e

            # Convert result to list of dicts efficiently
            batch = self._result_to_dicts(result)

            # If filter is a callable, always apply Python-side filtering
            # (even if SQL translation was attempted, as a safety net for type mismatches)
            if self._filter and callable(self._filter):
                batch = [row for row in batch if self._filter(row)]

            # Column filtering is now handled in _result_to_dicts() for efficiency

            self._current_batch = batch
            self._offset = batch_offset

    def read(self) -> dict:
        """Read single record efficiently"""
        # Calculate which batch we need
        batch_index = self._get_current_batch_index()
        batch_offset = self._get_batch_offset(batch_index)

        # Load batch if needed (simplified check)
        if self._offset != batch_offset or self._current_batch is None or len(self._current_batch) == 0:
            self._load_batch(batch_index)

        if not self._current_batch:
            raise StopIteration

        # Get item from current batch using position within batch
        position_in_batch = self.pos % self._batch_size
        if position_in_batch < len(self._current_batch):
            item = self._current_batch[position_in_batch]
            self.pos += 1
            return item
        else:
            # End of batch, load next batch
            self._load_batch(batch_index + 1)
            if not self._current_batch:
                raise StopIteration
            item = self._current_batch[0]
            self.pos += 1
            return item

    def read_bulk(self, num: int = 100) -> list[dict]:
        """Read bulk records efficiently"""
        self._ensure_connection()

        # Build SQL query with pushdown optimizations (using parameterized queries)
        query, params = self._build_sql_query(limit=num, offset=self.pos)
        try:
            result = self._connection.execute(query, params)
        except Exception as e:
            # Convert DuckDB errors to our exception hierarchy
            raise FormatParseError(
                format_id=self._file_format,
                message=f"Failed to execute query: {str(e)}",
                filename=self.filename,
            ) from e

        # Convert result to list of dicts efficiently
        chunk = self._result_to_dicts(result)

        # If filter is a callable, always apply Python-side filtering
        # (even if SQL translation was attempted, as a safety net for type mismatches)
        if self._filter and callable(self._filter):
            chunk = [row for row in chunk if self._filter(row)]

        # Column filtering is now handled in _result_to_dicts() for efficiency

        self.pos += len(chunk)
        return chunk


# Backwards-compatible alias (engine)
DuckDBIterable = DuckDBEngineIterable
