"""Recursive Descent Parser for MiniLang."""
from typing import List
from .ast_nodes import (
    Token, tokenize, Program, Assign, Print, If, While,
    BinaryOp, Number, Variable, ASTNode
)


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self, offset: int = 1) -> Token:
        idx = min(self.pos + offset, len(self.tokens) - 1)
        return self.tokens[idx]

    def consume(self, expected_type: str) -> Token:
        cur = self.current()
        if cur.type != expected_type:
            raise SyntaxError(f"Expected {expected_type} at line {cur.line}, got {cur.type} ('{cur.value}')")
        self.pos += 1
        return cur

    def match(self, *expected_types: str) -> bool:
        return self.current().type in expected_types

    def parse(self) -> Program:
        statements = []
        while not self.match("EOF"):
            statements.append(self.parse_statement())
        return Program(statements=statements)

    def parse_statement(self) -> ASTNode:
        if self.match("PRINT"):
            self.consume("PRINT")
            expr = self.parse_expr()
            self.consume("SEMI")
            return Print(expr=expr)

        elif self.match("IF"):
            self.consume("IF")
            self.consume("LPAREN")
            cond = self.parse_expr()
            self.consume("RPAREN")
            self.consume("LBRACE")
            then_body = []
            while not self.match("RBRACE") and not self.match("EOF"):
                then_body.append(self.parse_statement())
            self.consume("RBRACE")
            else_body = []
            if self.match("ELSE"):
                self.consume("ELSE")
                self.consume("LBRACE")
                while not self.match("RBRACE") and not self.match("EOF"):
                    else_body.append(self.parse_statement())
                self.consume("RBRACE")
            return If(cond=cond, then_body=then_body, else_body=else_body)

        elif self.match("WHILE"):
            self.consume("WHILE")
            self.consume("LPAREN")
            cond = self.parse_expr()
            self.consume("RPAREN")
            self.consume("LBRACE")
            body = []
            while not self.match("RBRACE") and not self.match("EOF"):
                body.append(self.parse_statement())
            self.consume("RBRACE")
            return While(cond=cond, body=body)

        elif self.match("IDENT"):
            name_tok = self.consume("IDENT")
            self.consume("ASSIGN")
            expr = self.parse_expr()
            self.consume("SEMI")
            return Assign(name=name_tok.value, expr=expr)

        else:
            cur = self.current()
            raise SyntaxError(f"Unexpected token '{cur.type}' ({cur.value}) at line {cur.line}")

    # Expression precedence: Comparison < Add/Sub < Mul/Div/Mod < Primary
    def parse_expr(self) -> ASTNode:
        return self.parse_comparison()

    def parse_comparison(self) -> ASTNode:
        node = self.parse_term()
        while self.match("EQ", "NEQ", "LT", "GT", "LE", "GE"):
            op = self.current().value
            self.consume(self.current().type)
            right = self.parse_term()
            node = BinaryOp(op=op, left=node, right=right)
        return node

    def parse_term(self) -> ASTNode:
        node = self.parse_factor()
        while self.match("PLUS", "MINUS"):
            op = self.current().value
            self.consume(self.current().type)
            right = self.parse_factor()
            node = BinaryOp(op=op, left=node, right=right)
        return node

    def parse_factor(self) -> ASTNode:
        node = self.parse_primary()
        while self.match("MUL", "DIV", "MOD"):
            op = self.current().value
            self.consume(self.current().type)
            right = self.parse_primary()
            node = BinaryOp(op=op, left=node, right=right)
        return node

    def parse_primary(self) -> ASTNode:
        if self.match("NUMBER"):
            tok = self.consume("NUMBER")
            return Number(value=tok.value)
        elif self.match("IDENT"):
            tok = self.consume("IDENT")
            return Variable(name=tok.value)
        elif self.match("LPAREN"):
            self.consume("LPAREN")
            expr = self.parse_expr()
            self.consume("RPAREN")
            return expr
        else:
            cur = self.current()
            raise SyntaxError(f"Expected primary expression at line {cur.line}, got {cur.type}")


def parse_code(code: str) -> Program:
    tokens = tokenize(code)
    return Parser(tokens).parse()

