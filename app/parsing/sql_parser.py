import sqlparse
from sqlparse.sql import Identifier
from sqlparse.tokens import DDL


def smart_split(text: str) -> list:
    """Splits by comma, but ignores commas that are inside parentheses.
    This prevents breaking apart things like DECIMAL(10,2) into two pieces."""
    parts = []
    current = ""
    depth = 0
    for char in text:
        if char == "(":
            depth += 1
            current += char
        elif char == ")":
            depth -= 1
            current += char
        elif char == "," and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += char
    if current.strip():
        parts.append(current)
    return parts


def parse_sql_file(file_path: str) -> dict:
    """
    Parses a .sql file (schema/migration file) and extracts:
    - table names
    - column names per table
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        sql_content = f.read()

    statements = sqlparse.parse(sql_content)

    result = {
        "file": file_path,
        "tables": []
    }

    for statement in statements:
        if statement.get_type() != "CREATE":
            continue

        table_name = None
        columns = []

        tokens = [t for t in statement.tokens if not t.is_whitespace]

        for i, token in enumerate(tokens):
            # Find the table name — comes right after CREATE TABLE
            if token.ttype is DDL and token.value.upper() == "CREATE":
                for next_token in tokens[i:]:
                    if isinstance(next_token, Identifier):
                        table_name = next_token.get_real_name()
                        break

            # Find the column definitions — inside the parentheses
            if isinstance(token, sqlparse.sql.Parenthesis):
                column_defs = smart_split(token.value.strip("()"))
                for col_def in column_defs:
                    col_def = col_def.strip()
                    if not col_def:
                        continue
                    col_name = col_def.split()[0].strip('`"[]')
                    if col_name.upper() not in ("PRIMARY", "FOREIGN", "UNIQUE", "CONSTRAINT", "KEY"):
                        columns.append(col_name)

        if table_name:
            result["tables"].append({
                "name": table_name,
                "columns": columns
            })

    return result


if __name__ == "__main__":
    import json
    test_file = "data/sample.sql"
    parsed = parse_sql_file(test_file)
    print(json.dumps(parsed, indent=2))