from datetime import datetime
from typing import Any, Dict, List
from enum import Enum
from dataclasses import is_dataclass
from decimal import Decimal


class XMLSerializer:

    def __init__(self, encoding: str = "utf-8", indent: str = "  "):
        self.encoding = encoding
        self.indent = indent
        self._current_indent = 0

    def serialize(self, obj: Any, root_tag: str = "root") -> str:
        self._current_indent = 0
        xml_content = self._to_xml(obj, root_tag)
        return f'<?xml version="1.0" encoding="{self.encoding}"?>\n{xml_content}'

    def _to_xml(self, obj: Any, tag: str) -> str:

        if obj is None:
            return self._indent(f'<{tag} nil="true" />')

        if isinstance(obj, (str, int, float, bool, Decimal)):
            return self._indent(f'<{tag}>{self._escape(str(obj))}</{tag}>')

        if isinstance(obj, datetime):
            return self._indent(f'<{tag} type="datetime">{obj.isoformat()}</{tag}>')

        if isinstance(obj, Enum):
            return self._indent(f'<{tag}>{obj.value}</{tag}>')

        if isinstance(obj, dict):
            return self._dict_to_xml(obj, tag)

        if isinstance(obj, (list, tuple, set)):
            return self._list_to_xml(obj, tag)

        if is_dataclass(obj):
            return self._dataclass_to_xml(obj, tag)

        if hasattr(obj, '__dict__'):
            return self._object_to_xml(obj, tag)

        return self._indent(f'<{tag} type="{type(obj).__name__}">{self._escape(str(obj))}</{tag}>')

    def _dict_to_xml(self, obj_dict: Dict[str, Any], tag: str) -> str:
        if not obj_dict:
            return self._indent(f'<{tag} />')

        result = [self._indent(f'<{tag}>')]
        self._current_indent += 1

        for key, value in obj_dict.items():
            original_key = key
            if not self._is_valid_xml_name(key):
                key = "item"
                attr = f' key="{self._escape(str(original_key))}"'
            else:
                attr = ""

            result.append(self._to_xml(value, key))

        self._current_indent -= 1
        result.append(self._indent(f'</{tag}>'))
        return '\n'.join(result)

    def _list_to_xml(self, obj_list: List[Any], tag: str) -> str:
        if not obj_list:
            return self._indent(f'<{tag} />')

        result = [self._indent(f'<{tag} type="list">')]
        self._current_indent += 1

        for i, item in enumerate(obj_list):
            result.append(self._to_xml(item, "item"))

        self._current_indent -= 1
        result.append(self._indent(f'</{tag}>'))
        return '\n'.join(result)

    def _dataclass_to_xml(self, obj: Any, tag: str) -> str:
        result = [self._indent(f'<{tag} type="{obj.__class__.__name__}">')]
        self._current_indent += 1

        for field_name in obj.__dataclass_fields__:
            value = getattr(obj, field_name, None)
            original_field_name = field_name
            if not self._is_valid_xml_name(field_name):
                field_name = "field"
                attr = f' name="{self._escape(original_field_name)}"'
            else:
                attr = ""

            result.append(self._to_xml(value, field_name))

        self._current_indent -= 1
        result.append(self._indent(f'</{tag}>'))
        return '\n'.join(result)

    def _object_to_xml(self, obj: Any, tag: str) -> str:
        result = [self._indent(f'<{tag} type="{obj.__class__.__name__}">')]
        self._current_indent += 1

        for attr_name, value in obj.__dict__.items():
            if attr_name.startswith('_'):
                continue

            original_attr_name = attr_name
            if not self._is_valid_xml_name(attr_name):
                attr_name = "property"
                attr = f' name="{self._escape(original_attr_name)}"'
            else:
                attr = ""

            result.append(self._to_xml(value, attr_name))

        self._current_indent -= 1
        result.append(self._indent(f'</{tag}>'))
        return '\n'.join(result)

    def _indent(self, text: str) -> str:
        return f"{self.indent * self._current_indent}{text}"

    def _escape(self, text: str) -> str:
        escape_map = {
            '<': '&lt;',
            '>': '&gt;',
            '&': '&amp;',
            '"': '&quot;',
            "'": '&apos;'
        }

        result = []
        for char in text:
            if char in escape_map:
                result.append(escape_map[char])
            elif ord(char) < 32 and char not in ('\t', '\n', '\r'):
                result.append(f'&#x{ord(char):02x};')
            else:
                result.append(char)

        return ''.join(result)

    def _is_valid_xml_name(self, name: str) -> bool:
        if not name or name[0] in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-', '.'):
            return False

        for char in name:
            if not (char.isalnum() or char in ('-', '_', ':', '.')):
                return False

        return True