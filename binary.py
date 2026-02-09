import struct

class BinTypes:
    TSTR = 0x01
    TLIST = 0x02
    TDICT = 0x03
    TINT = 0x04
    TFLOAT = 0x05
    TBOOL = 0x06

class BinSerializer:
    @staticmethod
    def serialize(obj):
        match obj:
            case bool():
                return BinSerializer._sbool(obj)
            case str():
                return BinSerializer._sstring(obj)
            case dict():
                return BinSerializer._sdict(obj)
            case list():
                return BinSerializer._slist(obj)
            case int():
                return BinSerializer._sint(obj)
            case float():
                return BinSerializer._sfloat(obj)
            case _:
                raise ValueError(f"Unsupported type: {type(obj)}")

    @staticmethod
    def _sstring(s):
        utf8_bytes = s.encode("utf-8")
        length = len(utf8_bytes)
        return struct.pack(">BI", BinTypes.TSTR, length) + utf8_bytes

    @staticmethod
    def _sdict(d):
        items = []
        for key, value in d.items():
            key_bytes = BinSerializer._sstring(key)
            value_bytes = BinSerializer.serialize(value)
            items.append(key_bytes + value_bytes)

        items_count = len(items)
        header = struct.pack(">BI", BinTypes.TDICT, items_count)
        return header + b"".join(items)

    @staticmethod
    def _slist(lst):
        items = [BinSerializer.serialize(item) for item in lst]
        items_count = len(items)
        header = struct.pack(">BI", BinTypes.TLIST, items_count)
        return header + b"".join(items)

    @staticmethod
    def _sint(value):
        return struct.pack(">Bq", BinTypes.TINT, value)

    @staticmethod
    def _sfloat(value):
        return struct.pack(">Bd", BinTypes.TFLOAT, value)

    @staticmethod
    def _sbool(value):
        return struct.pack(">B?", BinTypes.TBOOL, value)

    @staticmethod
    def deserialize(data):
        pos = 0

        def read_bytes(n):
            nonlocal pos
            result = data[pos : pos + n]
            pos += n
            return result

        def peek_type():
            return data[pos] if pos < len(data) else -1

        match peek_type():
            case BinTypes.TSTR:
                pos += 1
                length = struct.unpack(">I", read_bytes(4))[0]
                string_data = read_bytes(length)
                return string_data.decode("utf-8")

            case BinTypes.TDICT:
                pos += 1
                items_count = struct.unpack(">I", read_bytes(4))[0]
                result = {}

                for _ in range(items_count):
                    key = BinSerializer.deserialize(data[pos:])
                    pos += len(BinSerializer.serialize(key))
                    value = BinSerializer.deserialize(data[pos:])
                    pos += len(BinSerializer.serialize(value))
                    result[key] = value

                return result

            case BinTypes.TLIST:
                pos += 1
                items_count = struct.unpack(">I", read_bytes(4))[0]
                result = []

                for _ in range(items_count):
                    item = BinSerializer.deserialize(data[pos:])
                    item_size = len(BinSerializer.serialize(item))
                    pos += item_size
                    result.append(item)

                return result

            case BinTypes.TINT:
                pos += 1
                return struct.unpack(">q", read_bytes(8))[0]

            case BinTypes.TFLOAT:
                pos += 1
                return struct.unpack(">d", read_bytes(8))[0]

            case BinTypes.TBOOL:
                pos += 1
                return struct.unpack(">?", read_bytes(1))[0]

            case _:
                raise ValueError("Unknown type in binary data")
