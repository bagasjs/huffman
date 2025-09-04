from __future__ import annotations
import base64
import json

def shiftargs(args: list[str], error: str) -> tuple[str, list[str]]:
    if len(args) < 1:
        print(f"ERROR: {error}")
        exit(-1)
    return args[0], args[1:]

def display_token(token: str) -> str:
    if token.isprintable():
        return f"Token({token})"
    else:
        return f"Token({ord(token)})"

class Node(object):
    token: str
    freq: int
    lhs: Node | None
    rhs: Node | None

    def __init__(self, token: str, freq: int, lhs: Node | None, rhs: Node | None):
        self.token = token
        self.freq = freq
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self):
        if self.lhs != None and self.rhs != None:
            return f"Node(Link, Freq={self.freq})"
        else:
            return f"Node({display_token(self.token)}, Freq={self.freq})"

    def __repr__(self):
        return str(self)

def make_leaf_node(token: str, freq: int) -> Node:
    return Node(token, freq, None, None)

def make_link_node(lhs: Node, rhs: Node) -> Node:
    return Node("\0", lhs.freq + rhs.freq, lhs, rhs)

def dump_node(node: Node, level: int = 0):
    if node.lhs != None and node.rhs != None:
        dump_node(node.lhs, level + 1)
        dump_node(node.rhs, level + 1)
    print(">" * (level + 1), node)

class bitswriter(object):
    def __init__(self):
        self._ba  = bytearray()
        self._bits    = 0
        self._bitslen = 0 # Capped at 8 or a byte

    def tobytes(self) -> bytes:
        if self._bitslen > 0:
            self._ba.append(self._bits)
            self._bits = 0
            self._bitslen = 0
        return bytes(self._ba)

    def pushbit(self, value: bool):
        if value:
            self._bits |= (1 << (7 - self._bitslen))
        self._bitslen += 1

        if self._bitslen == 8:
            self._ba.append(self._bits)
            self._bits = 0
            self._bitslen = 0

    def pushbytes(self, value: bytes):
        for byte in value:
            for i in range(8):
                bit = (byte >> (7 - i)) & 1
                self.pushbit(bit == 1)

def get_encoding_of_token(token: str, root: Node) -> bytes:
    result = bitswriter()
    def get_encoding_of_token_inner(node: Node) -> bool:
        if node.lhs is None and node.rhs is None:
            return True if node.token == token else False
        if node.lhs is not None:
            found = get_encoding_of_token_inner(node.lhs)
            if found:
                result.pushbit(False)
                return True
        if node.rhs is not None:
            found = get_encoding_of_token_inner(node.rhs)
            if found:
                result.pushbit(True)
                return True
        return False

    found = get_encoding_of_token_inner(root)
    assert found, f"{display_token(token)} is invalid"
    return result.tobytes()

if __name__ == "__main__":
    import sys
    _, args = shiftargs(sys.argv, "Unreachable")
    path, _ = shiftargs(args, "Please provide a file path")
    with open(path, "r") as file:
        data = file.read()
    tokenfreqs = {}
    for ch in data:
        if ch in tokenfreqs:
            tokenfreqs[ch] += 1
        else:
            tokenfreqs[ch] = 1
    tokenfreqs = list(tokenfreqs.items())
    tokenfreqs.sort(key=lambda item: item[1])
    queue = [ make_leaf_node(token, freq) for token, freq in tokenfreqs ]
    while len(queue) > 1:
        lhs = queue.pop(0)
        rhs = queue.pop(0)
        node = make_link_node(lhs, rhs)
        where = len(queue) - 1
        for i in range(where + 1):
            if queue[i].freq > node.freq:
                where = i
                break
        queue.insert(where, node)
    assert len(queue) == 1
    root = queue.pop()
    table = {}
    for token, _ in tokenfreqs:
        table[token] = get_encoding_of_token(token, root)
    result = bitswriter()
    for ch in data:
        result.pushbytes(table[ch])
    with open("result.data", "wb") as file:
        file.write(result.tobytes())
    with open("result.table", "w") as file:
        new_table = {}
        for key, value in table.items():
            new_table[key] = base64.b64encode(value).decode()
        file.write(json.dumps(new_table, indent=4))
        

