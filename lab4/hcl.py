from enum import Enum, auto


class HclTokenType(Enum):
    L_BRACE = auto()
    R_BRACE = auto()
    EQUALS = auto()
    STRING = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    EOF = auto()


class HclParser:
    def __init__(self, raw_data):
        self.tokens = self._tokenize(raw_data)
        self.pos = 0

    @staticmethod
    def _tokenize(data):
        tokens = []
        current_token = ""
        in_quotes = False

        def save_identifier():
            nonlocal current_token
            if current_token:
                num_str = current_token
                if num_str.startswith('-'):
                    num_str = num_str[1:]

                if num_str.replace('.', '', 1).isdigit() and num_str.count('.') <= 1:
                    if '.' in current_token:
                        tokens.append((HclTokenType.NUMBER, float(current_token)))
                    else:
                        tokens.append((HclTokenType.NUMBER, int(current_token)))
                else:
                    tokens.append((HclTokenType.IDENTIFIER, current_token))
                current_token = ""

        i = 0
        while i < len(data):
            char = data[i]

            if in_quotes:
                if char == '"':
                    in_quotes = False
                    tokens.append((HclTokenType.STRING, current_token))
                    current_token = ""
                else:
                    current_token += char
                i += 1
            else:
                if char in '{}= \t\n':
                    save_identifier()

                    if char == '{':
                        tokens.append((HclTokenType.L_BRACE, "{"))
                    elif char == '}':
                        tokens.append((HclTokenType.R_BRACE, "}"))
                    elif char == '=':
                        tokens.append((HclTokenType.EQUALS, "="))

                    i += 1
                elif char == '"':
                    save_identifier()
                    in_quotes = True
                    i += 1
                else:
                    current_token += char
                    i += 1

        save_identifier()
        tokens.append((HclTokenType.EOF, ""))
        return tokens

    def _peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return HclTokenType.EOF, ""

    def _consume(self):
        token = self._peek()
        if token[0] != HclTokenType.EOF:
            self.pos += 1
        return token

    def parse(self):
        return self._parse_body()

    def _parse_body(self, context=None):
        if context is None:
            context = {}

        while True:
            token_type, token_val = self._peek()

            if token_type == HclTokenType.EOF or token_type == HclTokenType.R_BRACE:
                break

            if token_type == HclTokenType.IDENTIFIER:
                identifier = token_val
                self._consume()

                next_type, _ = self._peek()

                if next_type == HclTokenType.EQUALS:
                    self._parse_attribute(identifier, context)
                elif next_type == HclTokenType.L_BRACE:
                    self._consume()
                    if identifier in context:
                        if isinstance(context[identifier], list):
                            new_block = {}
                            context[identifier].append(new_block)
                            self._parse_body(new_block)
                        else:
                            old_block = context[identifier]
                            new_block = {}
                            context[identifier] = [old_block, new_block]
                            self._parse_body(new_block)
                    else:
                        new_block = {}
                        context[identifier] = [new_block]
                        self._parse_body(new_block)
                    self._consume()
                elif next_type in (HclTokenType.STRING, HclTokenType.IDENTIFIER):
                    block_name = identifier
                    labels = []

                    while True:
                        token_type, token_val = self._peek()
                        if token_type == HclTokenType.L_BRACE:
                            break
                        self._consume()
                        if token_type in (HclTokenType.STRING, HclTokenType.IDENTIFIER):
                            labels.append(token_val)
                        else:
                            raise SyntaxError(f"Expected label or '{{'")

                    self._consume()

                    block_data = {}
                    self._parse_body(block_data)

                    self._consume()

                    current = block_data
                    for label in reversed(labels):
                        current = {label: [current]}

                    if block_name in context:
                        if isinstance(context[block_name], list):
                            context[block_name].append(current)
                        else:
                            old = context[block_name]
                            context[block_name] = [old, current]
                    else:
                        context[block_name] = [current]
                else:
                    raise SyntaxError(f"Unexpected token after '{identifier}': {next_type}")
            else:
                raise SyntaxError(f"Expected IDENTIFIER, got {token_type}")

        return context

    def _parse_attribute(self, key, context):
        self._consume()

        val_token = self._consume()

        if val_token[0] in (HclTokenType.STRING, HclTokenType.IDENTIFIER, HclTokenType.NUMBER):
            context[key] = val_token[1]
        else:
            raise SyntaxError(f"Expected value for '{key}', got {val_token[0]}")