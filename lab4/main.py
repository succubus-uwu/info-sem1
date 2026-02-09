from binary import BinSerializer
from hcl import HclParser
from toml import TomlSerializer
from xml import XMLSerializer
import time
import hcl2
import rtoml


hcl_code = """
resource "aws_instance" "web" {
  ami           = "ami-a1b2c3d4"
  instance_type = "t2.micro"

  tags {
    Name = "HelloWorld"
  }
}
"""

# Обязательное задание

print("-"*50)
print("Обязательное задание")
print("-"*50)

def hcl_to_toml(input_text):
    lines = input_text.splitlines()
    result = []
    path_stack = []

    for line in lines:
        line = line.strip()

        if not line or line.startswith(('#', '//')):
            result.append(line)
            continue

        if '{' in line:
            header = line.split('{')[0].strip()
            parts = [p.strip('" ') for p in header.split() if p.strip()]

            path_stack.append(parts)
            full_path = ".".join([".".join(p) if isinstance(p, list) else p for p in path_stack])
            result.append(f"\n[{full_path}]")

        elif '}' in line:
            if path_stack:
                path_stack.pop()

        elif '=' in line:
            result.append(line)

    return "\n".join(result)

print(hcl_to_toml(hcl_code))

# Доп. 1

print("-"*50)
print("Доп. 1")
print("-"*50)

def convert_hcl_to_toml_rtoml(hcl_text):
    data = hcl2.loads(hcl_text)
    toml_text = rtoml.dumps(data)

    return toml_text

try:
    print(convert_hcl_to_toml_rtoml(hcl_code))
except Exception as e:
    print(f"Ошибка при конвертации: {e}")



# Доп. 2

print("-"*50)
print("Доп. 2")
print("-"*50)

import re


def hcl_to_toml_regex(input_text):
    lines = input_text.splitlines()
    result = []
    path_stack = []

    block_pattern = re.compile(r'^([\w\s"]+)\s*\{$')

    kv_pattern = re.compile(r'^([\w\d_-]+)\s*=\s*(.*)$')

    for line in lines:
        line = line.strip()

        if not line or re.match(r'^(#|//)', line):
            result.append(line)
            continue

        block_match = block_pattern.match(line)
        if block_match:
            header = block_match.group(1).strip()
            parts = re.findall(r'"([^"]*)"|(\S+)', header)
            clean_parts = [p[0] if p[0] else p[1] for p in parts]

            path_stack.append(clean_parts)
            full_path = ".".join([".".join(p) for p in path_stack])
            result.append(f"\n[{full_path}]")
            continue

        if line == '}':
            if path_stack:
                path_stack.pop()
            continue

        kv_match = kv_pattern.match(line)
        if kv_match:
            key = kv_match.group(1).strip()
            value = kv_match.group(2).strip()
            result.append(f"{key} = {value}")

    return "\n".join(result)

print(hcl_to_toml_regex(hcl_code))

hcl_code = """
schedule "thursday" {
  lecture {
    time      = "08:10"
    subject   = "Информатика"
    lecturer  = "Миняев Илья Андреевич"
    room      = "1328"
    address   = "Кронверкский пр., д.49, лит.А"
  }

  lecture {
    time      = "09:50"
    subject   = "Информатика"
    lecturer  = "Миняев Илья Андреевич"
    room      = "1328"
    address   = "Кронверкский пр., д.49, лит.А"
  }
}
"""

def measure_time(func, iterations=100):
    start_time = time.time()
    for _ in range(iterations):
        func()
    end_time = time.time()
    return (end_time - start_time) * 1000

def custom_parser_to_toml():
    parser = HclParser(hcl_code)
    parsed = parser.parse()
    toml_data = TomlSerializer.serialize(parsed)
    return toml_data

def custom_parser_to_xml():
    parser = HclParser(hcl_code)
    parsed = parser.parse()
    xml_data = XMLSerializer().serialize(parsed)
    return xml_data

def custom_parser_to_binary():
    parser = HclParser(hcl_code)
    parsed = parser.parse()
    binary_data = BinSerializer.serialize(parsed)
    return binary_data

def library_parser_to_toml():
    parsed = hcl2.loads(hcl_code)
    toml_data = rtoml.dumps(parsed)
    return toml_data

print("-"*50)
print("Измерение времени выполнения (100 итераций)")
print("-"*50)

time1 = measure_time(custom_parser_to_toml, 100)
print(f"1. Собственный парсер из HCL и сериализатор в TOML: {time1:.2f} мс")

time2 = measure_time(custom_parser_to_xml, 100)
print(f"2. Собственный сериализатор в XML: {time2:.2f} мс")

time3 = measure_time(custom_parser_to_binary, 100)
print(f"3. Собственный сериализатор в Binary: {time3:.2f} мс")

time4 = measure_time(library_parser_to_toml, 100)
print(f"4. Библиотечный hcl2 в rtoml: {time4:.2f} мс")

print("\nСравнение производительности:")
print(f"Скорость библиотечного решения относительно собственного (TOML): {time1/time4:.2f}x")


parser = HclParser(hcl_code)
parsed = parser.parse()

toml = TomlSerializer.serialize(parsed)

binary = BinSerializer.serialize(parsed)
deserialized = BinSerializer.deserialize(binary)

lib_parsed = hcl2.loads(hcl_code)
lib_toml = rtoml.dumps(lib_parsed)

xml = XMLSerializer().serialize(parsed)

with open("data/output.toml", "w", encoding="utf-8") as f:
    f.write(toml)

with open("data/output.bin", "wb") as f:
    f.write(binary)

with open("data/lib_output.toml", "w", encoding="utf-8") as f:
    f.write(lib_toml)

with open("data/output.xml", "w", encoding="utf-8") as f:
    f.write(xml)