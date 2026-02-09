from typing import Any, Dict


class TomlSerializer:
    @staticmethod
    def serialize(data: Dict[str, Any]) -> str:
        def escape_string(s: str) -> str:
            result = []
            for char in s:
                if char == '\\':
                    result.append('\\\\')
                elif char == '"':
                    result.append('\\"')
                elif char == '\b':
                    result.append('\\b')
                elif char == '\t':
                    result.append('\\t')
                elif char == '\n':
                    result.append('\\n')
                elif char == '\f':
                    result.append('\\f')
                elif char == '\r':
                    result.append('\\r')
                elif ord(char) < 0x20 or ord(char) == 0x7F:
                    result.append(f"\\u{ord(char):04x}")
                else:
                    result.append(char)
            return '"' + ''.join(result) + '"'

        def escape_key(key: str) -> str:
            if key == "":
                return escape_string(key)

            allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
            needs_escaping = False

            if key[0].isdigit():
                needs_escaping = True
            else:
                for char in key:
                    if char not in allowed_chars:
                        needs_escaping = True
                        break

            if needs_escaping:
                return escape_string(key)
            return key

        def is_array_of_tables(value: Any) -> bool:
            if not isinstance(value, list) or not value:
                return False

            return all(isinstance(item, dict) for item in value)

        def is_simple_inline_table(d: dict) -> bool:
            if not d:
                return True
            for value in d.values():
                if isinstance(value, dict):
                    return False
                if isinstance(value, list):
                    if value and isinstance(value[0], dict):
                        return False
            return True

        def serialize_value(value: Any, allow_inline_table: bool = True) -> str:
            if isinstance(value, str):
                return escape_string(value)
            if isinstance(value, bool):
                return "true" if value else "false"
            if isinstance(value, int):
                return str(value)
            if isinstance(value, float):
                if value == float('inf'):
                    return "inf"
                elif value == float('-inf'):
                    return "-inf"
                elif value != value:
                    return "nan"
                return str(value)
            if isinstance(value, list):
                if not value:
                    return "[]"

                if is_array_of_tables(value):
                    raise ValueError("Array of tables cannot be inline")

                items = [serialize_value(item, allow_inline_table=False) for item in value]
                return "[" + ", ".join(items) + "]"
            if isinstance(value, dict):
                if allow_inline_table and is_simple_inline_table(value):
                    if not value:
                        return "{}"
                    pairs = []
                    for k, v in value.items():
                        pairs.append(f"{escape_key(k)} = {serialize_value(v, allow_inline_table=False)}")
                    return "{ " + ", ".join(pairs) + " }"
                else:
                    raise ValueError("Non-inline table in value position")
            raise TypeError(f"Unsupported type: {type(value)}")

        def write_array_of_tables(array: list, path: list, output: list, add_blank_before_first: bool = True):
            for i, item in enumerate(array):
                if i > 0:
                    output.append("")
                elif add_blank_before_first and output and output[-1] != "":
                    output.append("")

                header = ".".join(escape_key(part) for part in path)
                output.append(f"[[{header}]]")

                write_item_contents(item, path, output)

        def has_only_array_of_tables(table: dict) -> bool:
            for value in table.values():
                if not is_array_of_tables(value):
                    return False
            return True

        def write_item_contents(table: dict, path: list, output: list):
            simple_values = []
            nested_tables = []
            array_of_tables_list = []

            for key, value in sorted(table.items()):
                if is_array_of_tables(value):
                    array_of_tables_list.append((key, value))
                elif isinstance(value, dict) and not is_simple_inline_table(value):
                    nested_tables.append((key, value))
                else:
                    simple_values.append((key, value))

            for key, value in simple_values:
                try:
                    output.append(f"{escape_key(key)} = {serialize_value(value)}")
                except ValueError:
                    nested_tables.append((key, value))

            for key, value in nested_tables:
                if not isinstance(value, dict):
                    continue

                if has_only_array_of_tables(value):
                    for nested_key, nested_array in sorted(value.items()):
                        if is_array_of_tables(nested_array):
                            write_array_of_tables(nested_array, path + [key, nested_key], output, add_blank_before_first=True)
                else:
                    if output and output[-1] != "":
                        output.append("")
                    nested_path = path + [key]
                    header = ".".join(escape_key(part) for part in nested_path)
                    output.append(f"[{header}]")
                    write_table_contents(value, nested_path, output)

            for key, array in array_of_tables_list:
                add_blank = len(simple_values) > 0 or len(nested_tables) > 0
                write_array_of_tables(array, path + [key], output, add_blank_before_first=add_blank)

        def write_table_contents(table: dict, path: list, res: list):
            simple_values = []
            nested_tables = []
            array_of_tables_list = []

            for key, value in sorted(table.items()):
                if is_array_of_tables(value):
                    array_of_tables_list.append((key, value))
                elif isinstance(value, dict) and not is_simple_inline_table(value):
                    nested_tables.append((key, value))
                else:
                    simple_values.append((key, value))

            for key, value in simple_values:
                try:
                    res.append(f"{escape_key(key)} = {serialize_value(value)}")
                except ValueError:
                    nested_tables.append((key, value))

            for key, value in nested_tables:
                if not isinstance(value, dict):
                    continue

                if has_only_array_of_tables(value):
                    nested_path = path + [key]
                    write_table_contents(value, nested_path, res)
                else:
                    if res and res[-1] != "":
                        res.append("")
                    nested_path = path + [key]
                    header = ".".join(escape_key(part) for part in nested_path)
                    res.append(f"[{header}]")
                    write_table_contents(value, nested_path, res)

            for key, array in array_of_tables_list:
                add_blank = len(simple_values) > 0 or len(nested_tables) > 0
                write_array_of_tables(array, path + [key], res, add_blank_before_first=add_blank)

        def serialize_section(table: dict, output: list):
            simple_values = []
            nested_tables = []
            array_of_tables_list = []

            for key, value in sorted(table.items()):
                if is_array_of_tables(value):
                    array_of_tables_list.append((key, value))
                elif isinstance(value, dict) and not is_simple_inline_table(value):
                    nested_tables.append((key, value))
                else:
                    simple_values.append((key, value))

            for key, value in simple_values:
                try:
                    output.append(f"{escape_key(key)} = {serialize_value(value)}")
                except ValueError:
                    nested_tables.append((key, value))

            for key, value in nested_tables:
                if output and output[-1] != "":
                    output.append("")
                header = ".".join(escape_key(part) for part in [key])
                output.append(f"[{header}]")
                write_table_contents(value, [key], output)

            for key, array in array_of_tables_list:
                write_array_of_tables(array, [key], output)

        output = []
        serialize_section(data, output)

        while output and output[-1] == "":
            output.pop()

        return "\n".join(output)