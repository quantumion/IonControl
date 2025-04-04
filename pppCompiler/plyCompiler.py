# GardenSnake - a parser generator demonstration program
#
# This implements a modified version of a subset of Python:
#  - only 'def', 'return' and 'if' statements
#  - 'if' only has 'then' clause (no elif nor else)
#  - single-quoted strings only, content in raw format
#  - numbers are decimal.Decimal instances (not integers or floats)
#  - no print statment; use the built-in 'print' function
#  - only < > == + - / * implemented (and unary + -)
#  - assignment and tuple assignment work
#  - no generators of any sort
#  - no ... well, no quite a lot

# Why?  I'm thinking about a new indentation-based configuration
# language for a project and wanted to figure out how to do it.  Once
# I got that working I needed a way to test it out.  My original AST
# was dumb so I decided to target Python's AST and compile it into
# Python code.  Plus, it's pretty cool that it only took a day or so
# from sitting down with Ply to having working code.

# This uses David Beazley's Ply from http://www.dabeaz.com/ply/

# This work is hereby released into the Public Domain. To view a copy of
# the public domain dedication, visit
# http://creativecommons.org/licenses/publicdomain/ or send a letter to
# Creative Commons, 543 Howard Street, 5th Floor, San Francisco,
# California, 94105, USA.
#
# Portions of this work are derived from Python's Grammar definition
# and may be covered under the Python copyright and license
#
#          Andrew Dalke / Dalke Scientific Software, LLC
#             30 August 2006 / Cape Town, South Africa

# Changelog:
#  30 August - added link to CC license; removed the "swapcase" encoding

# Modifications for inclusion in PLY distribution
import sys

sys.path.insert(0, "../..")
from ply import lex, yacc

from pppCompiler.Symbol import SymbolTable, FunctionSymbol, ConstSymbol, VarSymbol

##### Lexer ######
# import lex
import decimal

reserved = {
    "def": "DEF",
    "while": "WHILE",
    "if": "IF",
    "elif": "ELIF",
    "else": "ELSE",
    "return": "RETURN",
    "import": "IMPORT",
    "var": "TYPE",
    "const": "CONST",
    "parameter": "TYPE",
    "shutter": "TYPE",
    "masked_shutter": "TYPE",
    "trigger": "TYPE",
    "counter": "TYPE",
    "exitcode": "TYPE",
    "address": "TYPE"
}

tokens = [
    'NAME',
    'INTEGER',
    'NUMBER',  # Python decimals
    'STRING',  # single quoted strings only; syntax of raw strings
    'LPAR',
    'RPAR',
    'COLON',
    'EQ',
    'NEQ',
    'ASSIGN',
    'LT',
    'LE',
    'GT',
    'GE',
    'PLUS',
    'MINUS',
    'MULT',
    'DIV',
    'SHL',
    'SHR',
    'PLUSA',
    'MINUSA',
    'MULTA',
    'DIVA',
    'ANDA',
    'ORA',
    'SHLA',
    'SHRA',
    'WS',
    'NEWLINE',
    'COMMA',
    'SEMICOLON',
    'INDENT',
    'DEDENT',
    'ENDMARKER',
 ] + list(set(reserved.values()))


# t_NUMBER = r'\d+'
# taken from decmial.py but without the leading sign
def t_INTEGER(t):
    r"""((0x[a-fA-F0-9]+)|([0-9]+))"""
    t.value = int(t.value, 0)
    return t


def t_NUMBER(t):
    r"""(\d+(\.\d*)?|\.\d+)([eE][-+]? \d+)?"""
    t.value = decimal.Decimal(t.value)
    return t


def t_STRING(t):
    r"'([^\\']+|\\'|\\\\)*'"  # I think this is right ...
    t.value = t.value[1:-1].encode("latin-1").decode("unicode_escape")  # .swapcase() # for fun
    return t


t_COLON = r':'
t_EQ = r'=='
t_NEQ = r'!='
t_ASSIGN = r'='
t_LT = r'<'
t_LE = r'<='
t_GE = r'>='
t_SHL = r'<<'
t_SHR = r'>>'
t_GT = r'>'
t_PLUS = r'\+'
t_PLUSA = r'\+='
t_MINUS = r'-'
t_MINUSA = r'-='
t_MULT = r'\*'
t_MULTA = r'\*='
t_DIV = r'/'
t_DIVA = r'/='
t_ANDA = r'&='
t_ORA = r'\|='
t_SHLA = r'<<='
t_SHRA = r'>>='

t_COMMA = r','
t_SEMICOLON = r';'

# Ply nicely documented how to do this.


def t_NAME(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, "NAME")
    return t


# Putting this before t_WS let it consume lines with only comments in
# them so the latter code never sees the WS part.  Not consuming the
# newline.  Needed for "if 1: #comment"
def t_comment(t):
    r"[ ]*\043[^\n]*"  # \043 is '#'
    pass


# Whitespace
def t_WS(t):
    r' [ ]+ '
    if t.lexer.at_line_start and t.lexer.paren_count == 0:
        return t


# Don't generate newline tokens when inside of parenthesis, eg
#   a = (1,
#        2, 3)
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    t.type = "NEWLINE"
    if t.lexer.paren_count == 0:
        return t


def t_LPAR(t):
    r'\('
    t.lexer.paren_count += 1
    return t


def t_RPAR(t):
    r'\)'
    # check for underflow?  should be the job of the parser
    t.lexer.paren_count -= 1
    return t


def t_error(t):
    raise SyntaxError("Unknown symbol %r" % (t.value[0],))
    print("Skipping", repr(t.value[0]))
    t.lexer.skip(1)


## I implemented INDENT / DEDENT generation as a post-processing filter

# The original lex token stream contains WS and NEWLINE characters.
# WS will only occur before any other tokens on a line.

# I have three filters.  One tags tokens by adding two attributes.
# "must_indent" is True if the token must be indented from the
# previous code.  The other is "at_line_start" which is True for WS
# and the first non-WS/non-NEWLINE on a line.  It flags the check so
# see if the new line has changed indication level.

# Python's syntax has three INDENT states
#  0) no colon hence no need to indent
#  1) "if 1: go()" - simple statements have a COLON but no need for an indent
#  2) "if 1:\n  go()" - complex statements have a COLON NEWLINE and must indent
NO_INDENT = 0
MAY_INDENT = 1
MUST_INDENT = 2


# only care about whitespace at the start of a line
def track_tokens_filter(lexer, tokens):
    lexer.at_line_start = at_line_start = True
    indent = NO_INDENT
    saw_colon = False
    for token in tokens:
        token.at_line_start = at_line_start

        if token.type == "COLON":
            at_line_start = False
            indent = MAY_INDENT
            token.must_indent = False

        elif token.type == "NEWLINE":
            at_line_start = True
            if indent == MAY_INDENT:
                indent = MUST_INDENT
            token.must_indent = False

        elif token.type == "WS":
            assert token.at_line_start == True
            at_line_start = True
            token.must_indent = False

        else:
            # A real token; only indent after COLON NEWLINE
            if indent == MUST_INDENT:
                token.must_indent = True
            else:
                token.must_indent = False
            at_line_start = False
            indent = NO_INDENT

        yield token
        lexer.at_line_start = at_line_start


def _new_token(type, lineno):
    tok = lex.LexToken()
    tok.type = type
    tok.value = None
    tok.lineno = lineno
    tok.lexpos = 0
    return tok


# Synthesize a DEDENT tag
def DEDENT(lineno):
    return _new_token("DEDENT", lineno)


# Synthesize an INDENT tag
def INDENT(lineno):
    return _new_token("INDENT", lineno)


# Track the indentation level and emit the right INDENT / DEDENT events.
def indentation_filter(tokens):
    # A stack of indentation levels; will never pop item 0
    levels = [0]
    token = None
    depth = 0
    prev_was_ws = False
    for token in tokens:
        ##        if 1:
        ##            print "Process", token,
        ##            if token.at_line_start:
        ##                print "at_line_start",
        ##            if token.must_indent:
        ##                print "must_indent",
        ##            print

        # WS only occurs at the start of the line
        # There may be WS followed by NEWLINE so
        # only track the depth here.  Don't indent/dedent
        # until there's something real.
        if token.type == "WS":
            assert depth == 0
            depth = len(token.value)
            prev_was_ws = True
            # WS tokens are never passed to the parser
            continue

        if token.type == "NEWLINE":
            depth = 0
            if prev_was_ws or token.at_line_start:
                # ignore blank lines
                continue
            # pass the other cases on through
            yield token
            continue

        # then it must be a real token (not WS, not NEWLINE)
        # which can affect the indentation level

        prev_was_ws = False
        if token.must_indent:
            # The current depth must be larger than the previous level
            if not (depth > levels[-1]):
                raise IndentationError("expected an indented block")

            levels.append(depth)
            yield INDENT(token.lineno)

        elif token.at_line_start:
            # Must be on the same level or one of the previous levels
            if depth == levels[-1]:
                # At the same level
                pass
            elif depth > levels[-1]:
                raise IndentationError("indentation increase but not in new block")
            else:
                # Back up; but only if it matches a previous level
                try:
                    i = levels.index(depth)
                except ValueError:
                    raise IndentationError("inconsistent indentation")
                for _ in range(i + 1, len(levels)):
                    yield DEDENT(token.lineno)
                    levels.pop()

        yield token

    ### Finished processing ###

    # Must dedent any remaining levels
    if len(levels) > 1:
        assert token is not None
        for _ in range(1, len(levels)):
            yield DEDENT(token.lineno)


# The top-level filter adds an ENDMARKER, if requested.
# Python's grammar uses it.
def filter(lexer, add_endmarker=True):
    token = None
    tokens = iter(lexer.token, None)
    tokens = track_tokens_filter(lexer, tokens)
    for token in indentation_filter(tokens):
        yield token

    if add_endmarker:
        lineno = 1
        if token is not None:
            lineno = token.lineno
        yield _new_token("ENDMARKER", lineno)


# Combine Ply and my filters into a new lexer

class IndentLexer(object):
    def __init__(self, debug=0, optimize=0, lextab='lextab', reflags=0):
        self.lexer = lex.lex(debug=debug, optimize=optimize, lextab=lextab, reflags=reflags)
        self.token_stream = None

    def input(self, s, add_endmarker=True):
        self.lexer.paren_count = 0
        self.lexer.input(s)
        self.token_stream = filter(self.lexer, add_endmarker)

    def token(self):
        try:
            t = next(self.token_stream)
            return t
        except StopIteration:
            return None

    def token_gen(self):
        while True:
            yield next(self.token_stream)

# Parsing

precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MULT', 'DIV'),
)

# dictionary of names
names = {}

class Code:
    def __init__(self):
        self.code = ""
        self.codegen = None

class plyParser:
    tokens = tokens

    def __init__(self, lexer=None):
        if lexer is None:
            lexer = IndentLexer()
        self.lexer = lexer
        self.parser = yacc.yacc(module=self, start="file_input_end")
        self.symbols = SymbolTable()

    def p_file_input_end(self, p):
        """file_input_end : file_input ENDMARKER"""
        p[0] = p[1]

    def p_file_input(self, p):
        """file_input : file_input NEWLINE
                      | file_input stmt
                      | NEWLINE
                      | stmt"""
        p[0] = p[1]

    def p_stmt(self, p):
        """stmt : const_decl
                | type_decl
                | procedurecall"""
        p[0] = p[1]

    def p_const_decl(self, p):
        """const_decl : CONST NAME ASSIGN INTEGER"""
        name, value = p[2], p[4]
        self.symbols[name] = ConstSymbol(name, value)

    def p_type_decl(self, p):
        """type_decl : TYPE encoding_decl NAME NEWLINE
                     | TYPE encoding_decl NAME ASSIGN INTEGER NEWLINE
                     | TYPE encoding_decl NAME ASSIGN INTEGER NAME NEWLINE"""
        type_, encoding, name, value, unit = p[1], p[2], p[3], None, None
        try:
            value = p[5]
            unit = p[6]
        except IndexError:
            pass
        self.symbols[name] = VarSymbol(type_=type_, name=name, value=value, encoding=encoding, unit=unit)

    def p_empty(self, p):
        """empty :"""
        pass

    def p_encoding_decl(self, p):
        """encoding_decl : LT NAME GT
                         | empty"""
        p[0] = p[2] if len(p) == 4 else None

    # def p_while(self, p):
    #     """while_statement : WHILE comparison COLON INDENT statement_block DEDENT"""
    #     pass

    def p_procedurecall(self, p):
        """procedurecall : NAME LPAR args RPAR
                         | NAME LPAR kwargs RPAR
                         | NAME LPAR args COMMA kwargs RPAR"""
        name = p[1]
        args = p[3] if p.slice[3].type == 'args' else list()
        kwargs = p[5] if len(p) == 7 else (p[3] if p.slice[3].type == 'kwargs' else dict())
        procedure = self.symbols.getProcedure()
        code = [ "# line {0}: procedurecall {1}".format(p.slice[1].lineno, line(loc, text)) ]


    def p_args(self, p):
        """args : args COMMA NAME
                | NAME
                | empty"""
        if p[1] is None:
            p[0] = list()
        elif len(p) == 4:
            p[1].append(p[3])
            p[0] = p[1]
        else:
            p[0] = list((p[1], ))

    def p_kwargs(self, p):
        """kwargs : kwargs COMMA kwarg
                  | kwarg
                  | empty"""
        if len(p) == 4:
            key, value = p[3]
            p[1][key] = value
            p[0] = p[1]
        elif p[1] is None:
            p[0] = dict()
        else:
            p[0] = dict((p[1], ))

    def p_kwarg(self, p):
        """kwarg : NAME ASSIGN NAME"""
        p[0] = (p[1], p[3])

    # def p_comparison(self, p):
    #     """comparison : expression LT expression
    #                   | expression GT expression
    #                   | expression LE expression
    #                   | expression GE expression
    #                   | expression EQ expression
    #                   | expression NEQ expression"""
    #     pass

    def parse(self, code):
        self.lexer.input(code)
        result = self.parser.parse(lexer=self.lexer)
        return
