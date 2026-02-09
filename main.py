from binary import BinSerializer
from hcl import HclParser
from toml import TomlSerializer
from xml import XMLSerializer
import time
import hcl2
import rtoml

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

print("Измерение времени выполнения (100 итераций):")

time1 = measure_time(custom_parser_to_toml, 100)
print(f"1. Собственный парсер в TOML: {time1:.2f} мс")

time2 = measure_time(custom_parser_to_xml, 100)
print(f"2. Собственный парсер в XML: {time2:.2f} мс")

time3 = measure_time(custom_parser_to_binary, 100)
print(f"3. Собственный парсер в Binary: {time3:.2f} мс")

time4 = measure_time(library_parser_to_toml, 100)
print(f"4. Библиотечный hcl2 в rtoml: {time4:.2f} мс")

print("\nСравнение производительности:")
print(f"Скорость библиотечного решения относительно собственного (TOML): {time1/time4:.2f}x")

# Обязательное задание
parser = HclParser(hcl_code)
parsed = parser.parse()

toml = TomlSerializer.serialize(parsed)

# Доп. 1
binary = BinSerializer.serialize(parsed)
deserialized = BinSerializer.deserialize(binary)

# Доп. 2
lib_parsed = hcl2.loads(hcl_code)
lib_toml = rtoml.dumps(lib_parsed)

# Доп. 3
xml = XMLSerializer().serialize(parsed)

with open("data/output.toml", "w", encoding="utf-8") as f:
    f.write(toml)

with open("data/output.bin", "wb") as f:
    f.write(binary)

with open("data/lib_output.toml", "w", encoding="utf-8") as f:
    f.write(lib_toml)

with open("data/output.xml", "w", encoding="utf-8") as f:
    f.write(xml)