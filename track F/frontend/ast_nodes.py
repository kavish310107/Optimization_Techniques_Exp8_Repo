"""Frontend for MiniLang: Lexer, Tokens, and AST Definitions."""
import re
from dataclasses import dataclass
from typing import List, Optional, Any, Union


# --- Token Definition ---
@dataclass
class Token:
    type: str
    value: Any
    line: int


# Token specifications
TOKEN_SPEC = [
    ("NUMBER",   r"\d+"),
    ("IF",       r"\bif\b"),
    ("ELSE",     r"\belse\b"),
    ("WHILE",    r"\bwhile\b"),
    ("PRINT",    r"\bprint\b"),
    ("IDENT",    r"[a-zA-Z_][a-zA-Z0-9_]*"),
    ("ASSIGN",   r"="),
    ("PLUS",     r"\+"),
    ("MINUS",    r"-"),
    ("MUL",      r"\*"),
    ("DIV",      r"/"),
    ("MOD",      r"%"),
    ("EQ",       r"=="),
    ("NEQ",      r"!="),
    ("LE",       r"<="),
    ("GE",       r">="),
    ("LT",       r"<"),
    ("GT",       r">"),
    ("LPAREN",   r"\("),
    ("RPAREN",   r"\)"),
    ("LBRACE",   r"\{"),
    ("RBRACE",   r"\}"),
    ("SEMI",     r";"),
    ("SKIP",     r"[ \t]+"),
    ("NEWLINE",  r"\n"),
]

TOKEN_REGEX = "|".join(f"(?P<{pair[0]}>{pair[1]})" for pair in TOKEN_SPEC)


def tokenize(code: str) -> List[Token]:
    """Tokenize MiniLang source code."""
    tokens = []
    line_num = 1
    for mo in re.finditer(TOKEN_REGEX, code):
        kind = mo.lastgroup
        val = mo.group()
        if kind == "NEWLINE":
            line_num += 1
        elif kind == "SKIP":
            continue
        elif kind == "NUMBER":
            tokens.append(Token("NUMBER", int(val), line_num))
        else:
            tokens.append(Token(kind, val, line_num))
    tokens.append(Token("EOF", None, line_num))
    return tokens


# --- AST Node Definitions ---
@dataclass
class ASTNode:
    pass


@dataclass
class Program(ASTNode):
    statements: List[ASTNode]


@dataclass
class Assign(ASTNode):
    name: str
    expr: ASTNode


@dataclass
class Print(ASTNode):
    expr: ASTNode


@dataclass
class If(ASTNode):
    cond: ASTNode
    then_body: List[ASTNode]
    else_body: List[ASTNode]


@dataclass
class While(ASTNode):
    cond: ASTNode
    body: List[ASTNode]


@dataclass
class BinaryOp(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode


@dataclass
class Number(ASTNode):
    value: int


@dataclass
class Variable(ASTNode):
    name: str

