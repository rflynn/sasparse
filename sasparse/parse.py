# flake8: ignore=E501

# from copy import copy

from .syntax import SAS_EBNF
from simpleparse.parser import Parser

import sys

sys.setrecursionlimit(3000)


class ParseNode:
    def __init__(self, s, tag, start, end, child):
        self.tag = tag
        self.start = start
        self.end = end
        self.str = s[start:end]
        self.child = child

    def __repr__(self):
        if self.child:
            return '{}({})'.format(self.tag, self.child)
        else:
            return repr(self.str)

    def dump(self, indent=0):
        ins = ' ' * indent
        if self.child:
            return ('{}{}:\n{}'.format(ins, self.tag,
                    ''.join(c.dump(indent + 1) for c in self.child)))
        else:
            return '{}{}: {}\n'.format(ins, self.tag, repr(self.str))

    def filter(self, f):
        """remove ParseNodes recursively that do not return a truthy value for f(node)"""
        if not f(self):
            return None
        # new1 = copy(self)
        new1 = self
        new1.child = [x for x in [c.filter(f) for c in new1.child] if x]
        return new1

    def filterspace(self):
        return self.filter(lambda node: not node.tag.startswith('space'))

    @staticmethod
    def make(matches, s):
        nodes = []
        for tag, start, end, child in matches:
            n = ParseNode(s, tag, start, end,
                          ParseNode.make(child, s) if child else [])
            nodes.append(n)
        return nodes

    @staticmethod
    def make_with_invalid_tag():
        # for test coverage
        return ParseNode('', 'INVALID-TAG', 0, 0, None)


class AstNode:

    @classmethod
    def from_parsetree(cls, pt):
        return cls(pt.filterspace() if pt else pt)

    def __init__(self, pt):
        self.ast = pt

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               self.ast.dump(indent=4) if self.ast else repr(self.ast))


class Formattable:
    def format(self, opts):
        raise NotImplementedError


class FormatOptions:
    def __init__(self, raw=True, canonical=False, minify=False, **kw):
        self.raw = raw
        self.canonical = canonical
        self.minify = minify
        self.kw = kw


class SymIO:
    """
    Interface for defining the symbolic input and output variables of
    block-level statements for tracking data flow through a program
    """

    def symbols_in(self):
        """symbol input -- symbols that exist before that are input"""
        raise NotImplementedError

    def symbols_out(self):
        """symbol output -- symbols that are defined"""
        raise NotImplementedError

    def symbols_del(self):
        """symbols deleted -- symbols that are no longer available"""
        raise NotImplementedError


class SASDoc(Formattable):

    _sasparser = Parser(SAS_EBNF)

    def __init__(self, pt):
        self.pt = pt
        # print('SASDoc p:', pt)
        self.top = [t for t in [TopLevel.from_parsetree(p.child[0]) for p in pt] if t]
        assert None not in self.top

    def __repr__(self):
        return repr(self.top)

    def format(self, opts):
        return '\n'.join(t.format(opts) if isinstance(t, Formattable) else repr(t)
                         for t in self.top)

    def dump(self):
        for a in self.pt:
            a.dump()

    def walk(self, callback):
        raise NotImplementedError

    @classmethod
    def from_file(cls, filepath):
        with open(filepath) as f:
            return cls.from_fd(f)

    @classmethod
    def from_fd(cls, fd):
        return cls.from_string(fd.read())

    @classmethod
    def from_string(cls, text):
        ok, child, nextchar = cls._sasparser.parse(text, production='sas')
        if not ok or nextchar != len(text):
            raise cls.on_error(text, ok, child, nextchar)
        pt = ParseNode.make(child, text)
        print(pt)
        doc = cls(pt)
        return doc

    @staticmethod
    def on_error(text, ok, child, nextchar):
        if child:
            _, start, end, _ = child[-1]
            print(text[start:end])
        lineno = text[:nextchar].count('\n')
        line = text[:nextchar + 256].split('\n')[lineno]
        return Exception('Line {}: {}\n\tparse error: "{}..." '.format(
            lineno + 1, line, repr(text[nextchar:nextchar + 256])))


class Brackets:
    def __init__(self, pt):
        self.pt = pt

    @staticmethod
    def from_parsetree(pt):
        return Brackets(pt.filterspace())


class Space:
    def __init__(self, body):
        self.body = body

    @staticmethod
    def from_parsetree(pt):
        return Space(pt.child[0].str)


class Comment:
    def __init__(self, body):
        self.body = body

    def __repr__(self):
        return '{} {}'.format(self.__class__.__name__, repr(Comment.summarize(self.body)))

    @staticmethod
    def summarize(s):
        newlinepos = max(0, min(s.find('\r'), s.find('\n')))
        if newlinepos == 0:
            newlinepos = len(s)
        shortlen = min(50, len(s))
        newlen = min(newlinepos, shortlen)
        ellipsis = '...' if newlen < len(s) else ''
        return s[:newlen] + ellipsis

    @staticmethod
    def from_parsetree(pt):
        body = pt.child[0].str
        return Comment(body)


class ArrayStmt:
    def __init__(self, pt):
        self.pt = pt

    def __repr__(self):
        return '{}pt={}'.format(self.__class__.__name__, self.pt.dump(indent=4))

    @staticmethod
    def from_parsetree(pt):
        return ArrayStmt(pt.filterspace())


class AssignStmt:

    @staticmethod
    def from_parsetree(pt):
        return AssignStmt(pt.filterspace())

    def __init__(self, pt):
        self.pt = pt

    def __repr__(self):
        return '{}pt={}'.format(self.__class__.__name__, self.pt.dump(indent=4))

    def symbols_in(self):
        # TODO: return symbols on right side
        raise NotImplementedError

    def symbols_out(self):
        # TODO: return left side
        raise NotImplementedError


class EmptyStmt(AstNode):
    pass


class ExprStmt(AstNode):
    pass


class InputStmt(AstNode):
    pass


class DatalinesStmt(AstNode):
    pass


class Title:
    def __init__(self, kw, msg=None):
        self.kw = kw
        self.msg = msg

    def __repr__(self):
        return '{} {} {}'.format(self.__class__.__name__, self.kw, self.msg)

    @staticmethod
    def from_parsetree(pt):
        # print(pt.tag, pt.child[0].tag, pt)
        c = pt.filterspace().child[0]
        if c.tag == 'title_':
            return Title(c.str)
        msg = c.child
        return Title(c.tag, msg=msg)


class Footnote(AstNode):
    pass


class ElseStmt(AstNode):
    pass


class FormatStmt(AstNode):
    pass


class IfStmt(AstNode):
    pass


class LengthStmt(AstNode):
    pass


# Macro._map['macro_call'] = MacroCall

class Macro:

    _map = {
        'macro_call'
    }

    def __init__(self, pt):
        # FIXME: lazy catch-all for unimplemented macros
        self.pt = pt

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               self.pt.dump(indent=4))

    @staticmethod
    def from_parsetree(pt):
        c = pt.child[0]
        # print(c.tag, c.dump())
        if c.tag == 'macro_call':
            return MacroCall.from_parsetree(c)
        if c.tag == 'macro_call_stmt':
            return Macro(c)
        if c.tag == 'macro_comment':
            return Macro(c)
        if c.tag == 'macro_def':
            return Macro(c)
        if c.tag == 'macro_do_block':
            return Macro(c)
        if c.tag == 'macro_else':
            return Macro(c)
        if c.tag == 'macro_emailx':
            return Macro(c)
        if c.tag == 'macro_if':
            return Macro(c)
        if c.tag == 'macro_then':
            return Macro(c)
        if c.tag == 'macro_until':
            return Macro(c)
        if c.tag == 'macro_include':
            return Macro(c)
        if c.tag == 'macro_global':
            return Macro(c)
        if c.tag == 'macro_goto':
            return Macro(c)
        if c.tag == 'macro_label':
            return Macro(c)
        if c.tag == 'macro_let':
            return MacroLet.from_parsetree(c)
        if c.tag == 'macro_local':
            return Macro(c)
        if c.tag == 'macro_mend':
            return Macro(c)
        if c.tag == 'macro_put':
            return Macro(c)
        if c.tag == 'macro_symdel':
            return Macro(c)
        if c.tag == 'macro_sysfunc':
            return Macro(c)
        if c.tag == 'macro_syslput':
            return Macro(c)
        if c.tag == 'macro_qsysfunc':
            return Macro(c)
        if c.tag == 'macro_to':
            return Macro(c)
        raise NotImplementedError(c.tag)


class MacroLet(Macro):  # TODO: SymIO

    @staticmethod
    def from_parsetree(pt):
        c = pt.filterspace().child
        if len(c) == 3:
            _let, key, val = c
        elif len(c) == 2:
            _let, key = c
            val = None
        elif len(c) == 4:
            _let, key, val, _hanging_comma = c
        return MacroLet(key, val)

    def __init__(self, key, val):
        self.key = key
        self.val = val

    def __repr__(self):
        return '{} key={} val={}'.format(self.__class__.__name__,
                                         self.key,
                                         self.val.dump() if self.val else None)


class Options:

    @staticmethod
    def from_parsetree(pt):
        keyvals = pt.filterspace().child[1]
        return Options(keyvals)

    def __init__(self, keyvals):
        self.keyvals = keyvals

    def __repr__(self):
        return '{} keyvals={}'.format(self.__class__.__name__, self.keyvals)


class StringDQ(Formattable):

    @classmethod
    def from_parsetree(cls, pt):
        return cls(pt)

    def __init__(self, substrs):
        self.substrs = substrs
        assert len(substrs) == 1

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.substrs[0]))


class StringSQ(Formattable):

    @classmethod
    def from_parsetree(cls, pt):
        return cls(pt)

    def __init__(self, substrs):
        self.substrs = substrs
        assert len(substrs) == 1

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.substrs[0]))


class String(Formattable):

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        return cls(cls._clsmap[c.tag].from_parsetree(c.child))

    _clsmap = {
        'stringdq': StringDQ,
        'stringsq': StringSQ,
    }

    def __init__(self, s):
        self.s = s

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.s))


class SASIdentMacro(Formattable):

    @classmethod
    def from_parsetree(cls, pt):
        return cls(pt)

    def __init__(self, s):
        self.s = s

    def __repr__(self):
        return repr(self.s)


class LibnameClearStmt(Formattable, SymIO):

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        print('c', c)
        _libname, ident, _kwclear, _eos = c
        return cls(LibRef.from_parsetree(ident))

    def __init__(self, ident):
        self.ident = ident

    def __repr__(self):
        return '{}(ident={})'.format(self.__class__.__name__,
                                     repr(self.ident))

    def format(self, opts):
        return 'libname {} {}'.format(self.ident.format(opts), 'clear')

    def symbols_in(self):
        return []

    def symbols_out(self):
        return []

    def symbols_del(self):
        return [self.ident]


class LibnameDefStmt(Formattable, SymIO):

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        print('c', c)
        _libname, ident, saslib, _eos = c
        return cls(Ident.from_parsetree(ident),
                   String.from_parsetree(saslib))

    def __init__(self, ident, saslib):
        self.ident = ident
        self.saslib = saslib

    def __repr__(self):
        return '{}(ident={}, saslib={})'.format(self.__class__.__name__,
                                                repr(self.ident),
                                                repr(self.saslib))

    def format(self, opts):
        return 'libname {} {}'.format(self.ident, repr(self.saslib))

    def symbols_in(self):
        return []

    def symbols_out(self):
        return [self.ident]


class LibnameListStmt(Formattable):

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        print('c', c)
        _libname, ident, _kwlist, _eos = c
        return cls(Ident.from_parsetree(ident))

    def __init__(self, ident):
        self.ident = ident

    def __repr__(self):
        return '{}(ident={})'.format(self.__class__.__name__,
                                     repr(self.ident))

    def format(self, opts):
        return 'libname {} {}'.format(self.ident, 'list')


class LibnameMetaStmt(Formattable):

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        print('c', c)
        _libname, ident, _kwmeta, opts, _eos = c
        return cls(Ident.from_parsetree(ident))

    def __init__(self, ident, opts=None):
        self.ident = ident
        self.opts = opts

    def format(self, opts):
        return 'libname {} {}'.format(self.ident, 'meta')

    def __repr__(self):
        return '{}(ident={}, opts={})'.format(self.__class__.__name__,
                                              repr(self.ident),
                                              repr(self.opts))


class LibnameEngineStmt(Formattable, SymIO):

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        print('c', c)
        _libname, ident, engine, saslib, _eos = c
        return cls(ident, engine, String.from_parsetree(saslib))

    def __init__(self, ident, engine, saslib):
        self.ident = ident
        self.engine = engine
        self.saslib = saslib

    def __repr__(self):
        return '{} ident={} engine={} saslib={} '.format(self.__class__.__name__,
                                                         repr(self.ident),
                                                         repr(self.engine),
                                                         repr(self.saslib))

    def format(self, opts):
        return 'libname {} {} {}'.format(self.ident,
                                         self.engine,
                                         repr(self.saslib))

    def symbols_in(self):
        return []

    def symbols_out(self):
        return [self.ident]


class LibnameStmt(Formattable):

    _clsmap = {
        'libname_def': LibnameDefStmt,
        'libname_clear': LibnameClearStmt,
        'libname_engine': LibnameEngineStmt,
        'libname_list': LibnameListStmt,
        'libname_meta': LibnameMetaStmt,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0].filterspace()
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, stmt):
        self.stmt = stmt

    def __repr__(self):
        return repr(self.stmt)

    def format(self, opts):
        return self.stmt.format(opts)


class Ident(Formattable):

    @classmethod
    def from_parsetree(cls, pt):
        return cls(pt)

    def __init__(self, ident):
        self.ident = ident

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.ident)

    def format(self, opts):
        return self.ident


class Macrovar_(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        return cls(Ident.from_parsetree(pt.child[0]))

    def __init__(self, ident):
        self.ident = ident

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.ident)


class Macrovar(AstNode):

    _clsmap = {
        'macrovar_': Macrovar_,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, ident):
        self.ident = ident

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.ident)


class IdentMacro(Formattable):

    _clsmap = {
        'ident': Ident,
        'macrovar': Macrovar,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, pt):
        self.pt = pt

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.pt))

    def format(self, opts):
        return self.cls.format(opts)


class IdentMacroDotted(Formattable):

    _clsmap = {
        'identmacro': IdentMacro,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, ident):
        self.ident = ident

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.ident))

    def format(self, opts):
        return self.cls.format(opts)


class Identifier(Formattable):

    _clsmap = {
        'identmacrodotted': IdentMacroDotted,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, ident):
        self.ident = ident

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.ident))

    def format(self, opts):
        return self.cls.format(opts)


class PseudoIdent(Formattable):

    _clsmap = {
        'sas_identifier': Identifier,
    }

    def __init__(self, pt):
        self.pt = pt
        c = pt.child[0]
        self.cls = self._clsmap[c.tag](c)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.cls))

    def format(self, opts):
        return self.cls.format(opts)

    @classmethod
    def from_parsetree(cls, pt):
        return cls(pt)


class LibRef(Formattable):

    _clsmap = {
        'pseudoident': PseudoIdent,
    }

    def __init__(self, pt):
        self.pt = pt
        c = pt.child[0]
        self.cls = self._clsmap[c.tag](c)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               repr(self.cls))

    def format(self, opts):
        return self.cls.format(opts)

    @classmethod
    def from_parsetree(cls, pt):
        return cls(pt)


class FilenameStmt:

    @staticmethod
    def from_parsetree(pt):
        return FilenameStmt(pt.filterspace())

    def __init__(self, pt):
        self.pt = pt

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               self.pt.dump(indent=4))


class DataBodySet(SymIO):

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        name = c[0]
        opts = c[1] if len(c) > 1 else None
        return cls(name, opts)

    def __init__(self, name, opts):
        self.name = name
        self.opts = opts

    def __repr__(self):
        return '{}(name={}, opts={})'.format(self.__class__.__name__,
                                             repr(self.name),
                                             repr(self.opts))

    def symbols_in(self):
        return [self.name]

    def symbols_out(self):
        return []


class DataStmtSet(SymIO):

    @classmethod
    def from_parsetree(cls, pt):
        _kwset, sets = pt.child
        return cls(DataBodySets.from_parsetree(sets))

    def __init__(self, sets):
        self.sets = sets

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               repr(self.sets))

    def symbols_in(self):
        symbols = []
        for s in self.sets:
            if isinstance(s, SymIO):
                symbols.extend(s.symbols_in())
        return symbols

    def symbols_out(self):
        return []


class DataBodyStmt(SymIO):

    @classmethod
    def from_parsetree(cls, pt):
        ch = pt.child[0]
        cl = cls._clsmap.get(ch.tag)
        return cls(cl.from_parsetree(ch) if cl else ch)

    _clsmap = {
        'data_body_stmt_set': DataStmtSet,
    }

    def __init__(self, sets):
        self.sets = sets

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               repr(self.sets))

    def symbols_in(self):
        symbols = []
        if isinstance(self.sets, SymIO):
            symbols.extend(self.sets.symbols_in())
        return symbols

    def symbols_out(self):
        return []


class DataBodySets:

    @classmethod
    def from_parsetree(cls, pt):
        sets = [DataBodySet.from_parsetree(p) for p in pt.child]
        return cls(sets)

    def __init__(self, sets):
        self.sets = sets

    def __iter__(self):
        return iter(self.sets)

    def symbols(self):
        return [s.name for s in self.sets]

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               repr(self.sets))


class DataBody(SymIO):

    @classmethod
    def from_parsetree(cls, pt):
        return cls(map(DataBodyStmt.from_parsetree, pt.child))

    def __init__(self, stmts):
        self.stmts = list(stmts)

    def __iter__(self):
        return iter(self.stmts)

    def symbols_in(self):
        symbols = []
        for stmt in self.stmts:
            if isinstance(stmt, SymIO):
                symbols.extend(stmt.symbols_in())
        return symbols

    def symbols_out(self):
        return []

    def __repr__(self):
        return '{}(stmts={})'.format(self.__class__.__name__, repr(self.stmts))


class DataStmt(SymIO):

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.filterspace().child
        _kwdata, sets, body = c
        return cls(DataBodySets.from_parsetree(sets),
                   DataBody.from_parsetree(body))

    def __init__(self, sets, body):
        self.sets = sets
        self.body = body

    def __repr__(self):
        return '{}(in={}, out={}, sets={}, body={})'.format(
            self.__class__.__name__,
            self.symbols_in(),
            self.symbols_out(),
            repr(self.sets),
            repr(self.body))

    def symbols_in(self):
        return self.body.symbols_in()

    def symbols_out(self):
        return self.sets.symbols()


class Pattern(AstNode):
    pass


class ProcStmt:

    _clsmap = {}  # populated later

    @classmethod
    def from_parsetree(cls, pt):
        pt = pt.filterspace()
        # print('pt', pt)
        c = pt.child[0]
        # print('c.tag', c.tag)
        # print(c)
        # print(c.dump())
        cl = cls._clsmap.get(c.tag)
        if cl:
            return cl.from_parsetree(c)
        raise NotImplementedError(c.tag)

    def __init__(self, pt):
        self.pt = pt

    def __repr__(self):
        return '{}:\n{}'.format(self.__class__.__name__,
                                self.pt.dump(indent=4))

    @staticmethod
    def kwnorm(kw):
        return kw.lower()


class ProcCatalogStmt(AstNode):
    pass


class ProcCImportStmt(AstNode):
    pass


class ProcContentsStmt(AstNode):
    pass


class ProcCorrStmt(AstNode):
    pass


class ProcDatasetsStmt(AstNode):
    pass


class ProcExportStmt(AstNode):
    pass


class ProcFormatStmt(AstNode):
    pass


class ProcFreqStmt(AstNode):
    pass


class ProcGmapStmt(AstNode):
    pass


class ProcGremoveStmt(AstNode):
    pass


class ProcImportStmt(AstNode):
    pass


class ProcMeansStmt(AstNode):
    pass


class ProcOptionsStmt(AstNode):
    pass


class ProcPrintStmt(AstNode):
    pass


class ProcPwEncodeStmt(AstNode):
    pass


class ProcRankStmt(AstNode):
    pass


class ProcReportStmt(AstNode):
    pass


class ProcSGPlotStmt(AstNode):
    pass


class ProcSGPanelStmt(AstNode):
    pass


class ProcSortStmt(AstNode):
    pass


class SQLStarDot(AstNode):

    def __repr__(self):
        return self.ast.str


class SQLDotStar(AstNode):

    def __repr__(self):
        return self.ast.str


class SQLStar(AstNode):

    _clsmap = {
        'sql_dot_star': SQLDotStar,
        'sql_star_dot': SQLStarDot,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.item))

    def dump(self):
        return self.__repr__()


class SQLIdentMacro(AstNode):

    _clsmap = {
        'identmacro': IdentMacro,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.item))

    def dump(self):
        return self.__repr__()


class SQLNull(AstNode):

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SASFormat(AstNode):
    pass


class SQLSASIdentSpecial(AstNode):

    _clsmap = {
        'sas_format': SASFormat,
    }

    @classmethod
    def from_parsetree(cls, pt):
        if pt and pt.child:
            c = pt.child[0]
            # print('c.tag', c.tag)
            return cls(cls._clsmap[c.tag].from_parsetree(c))
        else:
            return None

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.item))

    def dump(self):
        return self.__repr__()


class SQLIdent:

    _clsmap = {
        'sql_identmacro': SQLIdentMacro,
        'sql_null': SQLNull,
        'sql_sas_ident_special': SQLSASIdentSpecial,
        'sql_star': SQLStar,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.item))

    def dump(self):
        return self.__repr__()


class SQLQueryCreateTable(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        # print('c', c)
        _create, _table, tablename = c[0:3]
        assert _create.str.lower() == 'create'
        assert _table.str.lower() == 'table'
        del c[0:3]
        filter_expr = None
        as_expr = None
        if c[0].tag == 'sas_sql_create_table_expr':
            filter_expr = c.pop(0)
        if c[0].str.lower() == 'as':
            c.pop(0)
        if c[0].tag == 'sql_expr_create_table_as':
            as_expr = c.pop(0)
        assert not c
        return cls(tablename,
                   filter_expr,
                   SQLExprCreateTableAs.from_parsetree(as_expr))

    def __init__(self, tablename, filter_expr, as_expr):
        self.tablename = tablename
        self.filter_expr = filter_expr
        self.as_expr = as_expr

    def __repr__(self):
        return '{}(tablename={}, filter_expr={}, as_expr={})'.format(
            self.__class__.__name__,
            repr(self.tablename),
            repr(self.filter_expr),
            repr(self.as_expr))


class SQLQuerySelect(AstNode):

    _clsmap = {
        # 'sql_expr_select' added later...
        'sql_query_create_table': SQLQueryCreateTable,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.item))

    def dump(self):
        return self.__repr__()


class SQLExprSubquery(AstNode):

    _clsmap = {
        'sql_query_select': SQLQuerySelect,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.item))

    def dump(self):
        return self.__repr__()


class Float(AstNode):
    pass


class Integer:

    @classmethod
    def from_parsetree(cls, pt):
        return cls(pt.str)

    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.n))


class Number(AstNode):

    _clsmap = {
        'float': Float,
        'integer': Integer,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.n))

    def dump(self):
        return self.__repr__()


class SQLStringpart(AstNode):

    _clsmap = {
        'string': String,
        'sas_identifier': Identifier,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, s):
        self.s = s

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.s))

    def dump(self):
        return self.__repr__()


class SQLStringparts(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        params = pt.child
        return cls(map(SQLStringpart.from_parsetree, params))

    def __init__(self, strparts):
        self.strparts = list(strparts)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.strparts))

    def dump(self):
        return self.__repr__()


class SASExprList(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        params = pt.child
        # print('c', c)
        return cls(list(map(SQLExpr.from_parsetree, params)))

    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.params))

    def dump(self):
        return self.__repr__()


class SASExprTuple:

    @classmethod
    def from_parsetree(cls, pt):
        expr_list = pt.child[0]
        # print('c', c)
        return cls(SASExprList.from_parsetree(expr_list))

    def __init__(self, expr_list):
        self.expr_list = expr_list

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.expr_list))

    def dump(self):
        return self.__repr__()


class SQLExprTuple(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        params = pt.child
        # print('c', c)
        return cls(list(map(SQLExpr.from_parsetree, params)))

    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.params))

    def dump(self):
        return self.__repr__()


class SQLOpUnaryDistinct(AstNode):

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLSASOpUnaryCalculated(AstNode):

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLSASOpNamed(AstNode):

    _clsmap = {
        'kwcalculated': SQLSASOpUnaryCalculated,
        'kwdistinct': SQLOpUnaryDistinct,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c', c)
        op = c
        return cls(cls._clsmap[op.tag].from_parsetree(op))

    def __init__(self, op):
        self.op = op

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.op))

    def dump(self):
        return self.__repr__()


class SQLOpUnaryNot(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLOpUnaryNotTilde(SQLOpUnaryNot):
    pass


class SQLOpUnaryMinus(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLOpUnary(AstNode):

    _clsmap = {
        'not': SQLOpUnaryNot,
        '-': SQLOpUnaryMinus,
        # '+': SQLOpUnaryMinus,
        '~': SQLOpUnaryNotTilde,
    }

    @classmethod
    def from_parsetree(cls, pt):
        print('pt', pt)
        op = pt
        # assert op.tag != 'sql_op_unary'
        return cls(cls._clsmap[op.str.lower()].from_parsetree(op))

    def __init__(self, op):
        self.op = op

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.op))

    def dump(self):
        return self.__repr__()


# SQLOpUnary._clsmap['sql_op_unary'] = SQLOpUnary


class SQLSASOpUnary(AstNode):

    _clsmap = {
        'sql_sas_op_named': SQLSASOpNamed,
        'sql_op_unary': SQLOpUnary,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c', c)
        op = c
        return cls(cls._clsmap[op.tag].from_parsetree(op))

    def __init__(self, op):
        self.op = op

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.op))

    def dump(self):
        return self.__repr__()


class SQLExprUnary(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        print('c', c)
        op, expr = c
        return cls(SQLSASOpUnary.from_parsetree(op),
                   SQLExpr.from_parsetree(expr))

    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

    def __repr__(self):
        return '{}(op={}, expr={})'.format(
            self.__class__.__name__,
            repr(self.op),
            repr(self.expr))

    def dump(self):
        return self.__repr__()


class SQLExprCaseWhen(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        print(c)
        _when = None
        whenexpr = None
        _then = None
        thenexpr = None
        _when, whenexpr, _then, thenexpr = c
        assert _when.str.lower() == 'when'
        assert whenexpr.tag == 'sql_expr'
        assert _then.str.lower() == 'then'
        assert thenexpr.tag == 'sql_expr'
        return cls(SQLExpr.from_parsetree(whenexpr),
                   SQLExpr.from_parsetree(thenexpr))

    def __init__(self, whenexpr, thenexpr):
        self.whenexpr = whenexpr
        self.thenexpr = thenexpr

    def __repr__(self):
        return '{}(when={}, then={})'.format(
            self.__class__.__name__,
            repr(self.whenexpr),
            repr(self.thenexpr))

    def dump(self):
        return self.__repr__()


class SQLExprCaseWhenList(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        params = pt.child
        # print('c', c)
        return cls(list(map(SQLExprCaseWhen.from_parsetree, params)))

    def __init__(self, whens):
        self.whens = whens

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.whens))

    def dump(self):
        return self.__repr__()


class SQLExprCaseElse(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        if pt is None:
            return None
        c = pt.child
        print(c)
        _else = None
        expr = None
        _else, expr = c
        assert _else.str.lower() == 'else'
        assert expr.tag == 'sql_expr'
        return cls(SQLExpr.from_parsetree(expr))

    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.expr))

    def dump(self):
        return self.__repr__()


class SQLExprCase(AstNode):

    @classmethod
    def from_parsetree(cls, pt):

        c = pt.child

        _case = None
        thens = None
        else_expr = None
        _end = None

        if len(c) == 4:
            _case, thens, else_expr, _end = c
        elif len(c) == 3:
            _case, thens, _end = c
        else:
            raise NotImplementedError(c)

        assert _case.str.lower() == 'case'
        assert thens.tag == 'sql_expr_case_when_list'
        assert else_expr is None or else_expr.tag == 'sql_expr_case_else'
        assert _end.str.lower() == 'end'

        return cls(SQLExprCaseWhenList.from_parsetree(thens),
                   SQLExprCaseElse.from_parsetree(else_expr))

    def __init__(self, thens, else_expr):
        self.thens = thens
        self.else_expr = else_expr

    def __repr__(self):
        return '{}(then={}, else={})'.format(
            self.__class__.__name__,
            repr(self.thens),
            repr(self.else_expr))

    def dump(self):
        return self.__repr__()


class SQLFuncnameBuiltin(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print(c)
        # print('c.tag', c.tag)
        ident = c
        return cls(ident)

    def __init__(self, funcall):
        self.funcall = funcall

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.funcall))

    def dump(self):
        return self.__repr__()


class SQLExprList(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        params = pt.child
        # print('c', c)
        return cls(list(map(SQLExpr.from_parsetree, params)))

    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.params))

    def dump(self):
        return self.__repr__()


class SQLFuncallParams(AstNode):

    _clsmap = {
        'sql_expr_list': SQLExprList,
    }

    @classmethod
    def from_parsetree(cls, pt):
        if not pt.child:
            return cls([])  # empty list
        c = pt.child[0]
        # print('c', c)
        params = c
        return cls(cls._clsmap[params.tag].from_parsetree(params))

    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.params))

    def dump(self):
        return self.__repr__()


class FuncPutParams(AstNode):
    pass


class SASFuncallBuiltinPut(AstNode):

    _clsmap = {
        'func_put_params': FuncPutParams,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        print(c)
        assert len(c) == 1
        # print('c.tag', c.tag)
        params = c
        return cls(cls._clsmap[params.tag].from_parsetree(params))

    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return '{}(params={})'.format(
            self.__class__.__name__,
            repr(self.params))

    def dump(self):
        return self.__repr__()


class SQLFuncallBuiltin(AstNode):

    _clsmap = {
        'sql_funcname_builtin': SQLFuncnameBuiltin,
        'sql_funcall_params': SQLFuncallParams,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        print(c)
        assert len(c) == 2
        # print('c.tag', c.tag)
        ident, params = c
        return cls(cls._clsmap[ident.tag].from_parsetree(ident),
                   cls._clsmap[params.tag].from_parsetree(params))

    def __init__(self, ident, params):
        self.ident = ident
        self.params = params

    def __repr__(self):
        return '{}(ident={}, params={})'.format(
            self.__class__.__name__,
            repr(self.ident),
            repr(self.params))

    def dump(self):
        return self.__repr__()


class SQLFuncallUDF(AstNode):

    _clsmap = {
        'sql_ident': SQLIdent,
        'sql_funcall_params': SQLFuncallParams,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        print(c)
        assert len(c) == 2
        # print('c.tag', c.tag)
        ident, params = c
        return cls(cls._clsmap[ident.tag].from_parsetree(ident),
                   cls._clsmap[params.tag].from_parsetree(params))

    def __init__(self, ident, params):
        self.ident = ident
        self.params = params

    def __repr__(self):
        return '{}(ident={}, params={})'.format(
            self.__class__.__name__,
            repr(self.ident),
            repr(self.params))

    def dump(self):
        return self.__repr__()


class HangingComma(AstNode):
    pass


class MacroParamDef(AstNode):
    pass


class MacroParamList(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        # print('pt', pt)
        c = pt.child
        params = []
        comma = None
        if c[-1].tag == 'hanging_comma':
            comma = c.pop()
        params = c
        return cls(map(SASFuncallParam.from_parsetree, params),
                   HangingComma.from_parsetree(comma) if comma else None)

    def __init__(self, params, comma):
        self.params = list(params)
        self.comma = comma

    def __repr__(self):
        return '{}(params={}, comma={})'.format(
            self.__class__.__name__,
            repr(self.params),
            repr(self.comma))

    def dump(self):
        return self.__repr__()


class MacroParams:

    @classmethod
    def from_parsetree(cls, pt):
        params = None
        if pt is not None and pt.child:
            params = pt.child[0]
            return cls(MacroParamList.from_parsetree(params))
        else:
            return None

    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.params))

    def dump(self):
        return self.__repr__()


class MacroCallUDF:

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        # print('c.tag', c.tag)
        ident = c[0]
        params = None
        if len(c) > 1:
            params = c[1]
        return cls(ident,
                   MacroParams.from_parsetree(params))

    def __init__(self, ident, params):
        self.ident = ident
        self.params = params

    def __repr__(self):
        return '{}(ident={}, params={})'.format(
            self.__class__.__name__,
            repr(self.ident),
            repr(self.params))

    def dump(self):
        return self.__repr__()


class MacroCallLength(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        print(c)
        assert len(c) == 2
        # print('c.tag', c.tag)
        _ident, params = c
        return cls(MacroParams.from_parsetree(params))

    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return '{}(params={})'.format(
            self.__class__.__name__,
            repr(self.params))

    def dump(self):
        return self.__repr__()


class MacroCallBuiltin:

    _clsmap = {
        'macro_length': MacroCallLength,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, call):
        self.call = call

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.call)


class MacroCall:

    _clsmap = {
        'macro_call_udf': MacroCallUDF,
        'macro_call_builtin': MacroCallBuiltin,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print(c)
        # print('c.tag', c.tag)
        funcall = c
        return cls(cls._clsmap[funcall.tag].from_parsetree(funcall))

    def __init__(self, funcall):
        self.funcall = funcall

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.funcall))

    def dump(self):
        return self.__repr__()


class SASFuncallBuiltin(AstNode):

    _clsmap = {
        'sas_funcall_put': SASFuncallBuiltinPut,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        print(c)
        if c[0].tag == 'sas_funcall_put':
            return SASFuncallBuiltinPut(c)
        assert len(c) == 2
        # print('c.tag', c.tag)
        ident, params = c
        return cls(cls._clsmap[ident.tag].from_parsetree(ident),
                   cls._clsmap[params.tag].from_parsetree(params))

    def __init__(self, ident, params):
        self.ident = ident
        self.params = params

    def __repr__(self):
        return '{}(ident={}, params={})'.format(
            self.__class__.__name__,
            repr(self.ident),
            repr(self.params))

    def dump(self):
        return self.__repr__()


class SASFuncIdent(AstNode):

    _clsmap = {
        'ident': Ident,
    }

    @classmethod
    def from_parsetree(cls, pt):
        ident = pt.child[0]
        return cls(cls._clsmap[ident.tag].from_parsetree(ident))

    def __init__(self, ident):
        self.ident = ident

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.ident))

    def dump(self):
        return self.__repr__()


class SASFuncallParam(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        if pt and pt.child:
            c = pt.child[0]
            print('c', c)
            return cls(SASExprList.from_parsetree(c))
        else:
            return None

    def __init__(self, exprs):
        self.exprs = exprs

    def __repr__(self):
        return '{}(exprs={})'.format(
            self.__class__.__name__,
            repr(self.exprs))

    def dump(self):
        return self.__repr__()


class SASFuncallParamList(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        # print('pt', pt)
        c = pt.child
        params = []
        comma = None
        if c[-1].tag == 'hanging_comma':
            comma = c.pop()
        params = c
        return cls(map(SASFuncallParam.from_parsetree, params),
                   HangingComma.from_parsetree(comma) if comma else None)

    def __init__(self, params, comma):
        self.params = list(params)
        self.comma = comma

    def __repr__(self):
        return '{}(params={}, comma={})'.format(
            self.__class__.__name__,
            repr(self.params),
            repr(self.comma))

    def dump(self):
        return self.__repr__()


class SASFuncallParams(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        print('c', c)
        return cls(SASFuncallParamList.from_parsetree(c))

    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return '{}(params={})'.format(
            self.__class__.__name__,
            repr(self.params))

    def dump(self):
        return self.__repr__()


class SASFuncallUDF(AstNode):

    _clsmap = {
        'sas_func_ident': SASFuncIdent,
        'sas_funcall_params': SASFuncallParams,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        print(c)
        assert len(c) == 2
        # print('c.tag', c.tag)
        ident, params = c
        return cls(cls._clsmap[ident.tag].from_parsetree(ident),
                   cls._clsmap[params.tag].from_parsetree(params))

    def __init__(self, ident, params):
        self.ident = ident
        self.params = params

    def __repr__(self):
        return '{}(ident={}, params={})'.format(
            self.__class__.__name__,
            repr(self.ident),
            repr(self.params))

    def dump(self):
        return self.__repr__()


class SASFuncall(AstNode):

    _clsmap = {
        'sas_funcall_builtin': SASFuncallBuiltin,
        'sas_funcall_udf': SASFuncallUDF,
        'macro_call': MacroCall,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        funcall = c
        return cls(cls._clsmap[funcall.tag].from_parsetree(funcall))

    def __init__(self, funcall):
        self.funcall = funcall

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.funcall))

    def dump(self):
        return self.__repr__()


class SQLFuncall(AstNode):

    _clsmap = {
        'sas_funcall_builtin': SASFuncallBuiltin,
        'sas_funcall_udf': SASFuncallUDF,
        'sql_funcall_builtin': SQLFuncallBuiltin,
        'sql_funcall_udf': SQLFuncallUDF,
        'macro_call': MacroCall,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        funcall = c
        return cls(cls._clsmap[funcall.tag].from_parsetree(funcall))

    def __init__(self, funcall):
        self.funcall = funcall

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.funcall))

    def dump(self):
        return self.__repr__()


class SASBrackets(AstNode):

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.ast.str)


class DateLiteral(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(String.from_parsetree(c))

    def __init__(self, s):
        self.s = s

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.s))

    def dump(self):
        return self.__repr__()


class SQLExprScalar:

    _clsmap = {
        'date_literal': DateLiteral,
        'number': Number,
        'sas_brackets': SASBrackets,
        'sas_expr_tuple': SASExprTuple,
        'sql_funcall': SQLFuncall,
        'sql_expr_case': SQLExprCase,
        'sql_expr_subquery': SQLExprSubquery,
        'sql_expr_tuple': SQLExprTuple,
        'sql_expr_unary': SQLExprUnary,
        'sql_ident': SQLIdent,
        'sql_stringparts': SQLStringparts,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.item))

    def dump(self):
        return self.__repr__()


class SQLExprBinOp:

    @classmethod
    def from_parsetree(cls, pt):

        c = pt.child
        # print('c', c)

        left = None
        op_right = None

        if c and c[0].tag == 'sql_expr_scalar':
            left = c.pop(0)
        if c and c[0].tag == 'sql_expr_bin_op_val':
            op_right = c.pop(0)
        assert not c

        return cls(SQLExprScalar.from_parsetree(left),
                   SQLExprBinOpVal.from_parsetree(op_right))

    def __init__(self, left, op_right):
        self.left = left
        self.op_right = op_right

    def __repr__(self):
        return '{}(left={}, op_right={})'.format(
            self.__class__.__name__,
            repr(self.left),
            repr(self.op_right))

    def dump(self):
        return self.__repr__()


class SQLValue:

    _clsmap = {
        'sql_expr_scalar': SQLExprScalar,
        'sql_expr_binop': SQLExprBinOp,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.item))

    def dump(self):
        return self.__repr__()


class IdentMacro(AstNode):

    _clsmap = {
        'ident': Ident,
        'macrovar': Macrovar,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.item))

    def dump(self):
        return self.__repr__()


class IdentMacroDotted(AstNode):

    _clsmap = {
        'identmacro': IdentMacro,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.item))

    def dump(self):
        return self.__repr__()


class SASIdentifier(AstNode):

    _clsmap = {
        'identmacrodotted': IdentMacroDotted,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.item))

    def dump(self):
        return self.__repr__()


class SASOpUnaryMinus(AstNode):
    pass


class SASOpUnary(AstNode):
    pass


class SASExprUnary(AstNode):

    _map = {
        '-': SASOpUnaryMinus,
        'sas_op_unary': SASOpUnary,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        print('c', c)
        op, expr = c
        return cls(cls._map[op.tag].from_parsetree(op),
                   cls._map[expr.tag].from_parsetree(expr))

    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

    def __repr__(self):
        return '{}(op={}, expr={})'.format(
            self.__class__.__name__,
            repr(self.op),
            repr(self.expr))

    def dump(self):
        return self.__repr__()


class SASExprScalar(AstNode):

    _clsmap = {
        'macro': Macro,
        'number': Number,
        'sas_expr_tuple': SASExprTuple,
        'sas_expr_unary': SASExprUnary,
        'sas_funcall': SASFuncall,
        'sas_identifier': SASIdentifier,
        'sql_expr_tuple': SQLExprTuple,  # XXX: this shouln't be
        'string': String,
        'date_literal': DateLiteral,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.item))

    def dump(self):
        return self.__repr__()


class SQLOpBinCmp(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLOpBinLogicOr(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLOpBinLogicGreaterThan(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLOpBinLogicGreaterThanOrEqual(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLOpBinLogicLessThan(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLOpBinLogicLessThanOrEqual(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLOpBinArithMinus(AstNode):

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLOpBinConcat(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLOpBinLogicLike(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLOpBinLogicIn(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLOpBinLogicIs(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLOpBinLogicNot(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SASOpBin(AstNode):

    _strmap = {
        '=': SQLOpBinCmp,
        'or': SQLOpBinLogicOr,
        '>': SQLOpBinLogicGreaterThan,
        '>=': SQLOpBinLogicGreaterThanOrEqual,
        '<': SQLOpBinLogicLessThan,
        '<=': SQLOpBinLogicLessThanOrEqual,
        '-': SQLOpBinArithMinus,
        '||': SQLOpBinConcat,
        'like': SQLOpBinLogicLike,
        'in': SQLOpBinLogicIn,
        'is': SQLOpBinLogicIs,
        'not': SQLOpBinLogicNot,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt
        print('c', c)
        return cls(cls._strmap[c.str.lower()].from_parsetree(c))

    def __init__(self, op):
        self.op = op

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.op)

    def dump(self):
        return self.__repr__()


class SASExprBinGeneral(AstNode):

    _clsmap = {
        'sas_op_bin': SASOpBin,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        print('c', c)
        op, expr = c
        return cls(cls._clsmap[op.tag].from_parsetree(op),
                   cls._clsmap[expr.tag].from_parsetree(expr))

    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

    def __repr__(self):
        return '{}(op={}, expr={})'.format(
            self.__class__.__name__,
            repr(self.op),
            repr(self.expr))

    def dump(self):
        return self.__repr__()


class SASOpBetween(AstNode):
    pass


class SASExprBinOpVal(AstNode):

    _clsmap = {
        'sas_expr_bin_general': SASExprBinGeneral,
        'sas_op_between': SASOpBetween,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        print('c', c)
        op = c
        return cls(cls._clsmap[op.tag].from_parsetree(op))

    def __init__(self, op):
        self.op = op

    def __repr__(self):
        return '{}(op={})'.format(
            self.__class__.__name__,
            repr(self.op))

    def dump(self):
        return self.__repr__()


class SASExprBinOp(AstNode):

    _clsmap = {
        'sas_expr_scalar': SASExprScalar,
        'sas_expr_bin_op_val': SASExprBinOpVal,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        left, op_val = c
        return cls(cls._clsmap[left.tag].from_parsetree(left),
                   cls._clsmap[op_val.tag].from_parsetree(op_val))

    def __init__(self, left, op_val):
        self.left = left
        self.op_val = op_val

    def __repr__(self):
        return '{}(left={}, op_val={})'.format(
            self.__class__.__name__,
            repr(self.left),
            repr(self.op_val))

    def dump(self):
        return self.__repr__()


class SASValue(AstNode):

    _clsmap = {
        'sas_expr_scalar': SASExprScalar,
        'sas_expr_binop': SASExprBinOp,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.item))

    def dump(self):
        return self.__repr__()


class SASExpr:

    _clsmap = {
        'sql_value': SQLValue,
        'sas_value': SASValue,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.item))

    def dump(self):
        return self.__repr__()


SASExprBinGeneral._clsmap['sas_expr'] = SASExpr
SASExprUnary._map['sas_expr'] = SASExpr


class SQLExpr:

    _clsmap = {
        'sql_value': SQLValue,
        'sas_expr': SASExpr,
        'sas_expr_list': SASExprList,
        'sas_value': SASValue,
        'pseudoident': PseudoIdent,
    }

    @classmethod
    def from_parsetree(cls, pt):
        print('pt', pt)
        if pt.child:
            c = pt.child[0]
            # print('c.tag', c.tag)
            return cls(cls._clsmap[c.tag].from_parsetree(c))
        else:
            return None

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.item))

    def dump(self):
        return self.__repr__()


SQLExpr._clsmap['sql_expr'] = SQLExpr


class SQLOpBinIn(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLOpBinIs(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLOpBinLogicNot(AstNode):

    _clsmap = {
        'sql_op_bin_in': SQLOpBinIn,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        assert len(c) == 2
        _not, expr = c
        assert _not.str.lower() == 'not'
        print('c', c)
        return cls(cls._clsmap[expr.tag].from_parsetree(expr))

    def __init__(self, foo):
        self.foo = foo

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.foo)

    def dump(self):
        return self.__repr__()


SQLOpBinLogicNot._clsmap['sql_op_bin_not_in'] = SQLOpBinLogicNot


class SQLOpBinLogicAnd(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


SASOpBin._strmap['and'] = SQLOpBinLogicAnd


class SQLOpBinLogic(AstNode):

    _clsmap = {
        'kwand': SQLOpBinLogicAnd,
        'kwin': SQLOpBinIn,
        'kwis': SQLOpBinIs,
        'kwor': SQLOpBinLogicOr,
        'sql_op_bin_not_in': SQLOpBinLogicNot,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        print('c', c)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, foo):
        self.foo = foo

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.foo)

    def dump(self):
        return self.__repr__()


class SQLOpBinArithExp(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLOpBinDiv(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLOpBinOp(AstNode):

    _strmap = {
        '**': SQLOpBinArithExp,
        '||': SQLOpBinConcat,
        '/': SQLOpBinDiv,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt
        print('c', c)
        return cls(cls._strmap[c.str].from_parsetree(c))

    def __init__(self, op):
        self.op = op

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.op)

    def dump(self):
        return self.__repr__()


class SQLOpBin(AstNode):

    _clsmap = {
        'sql_op_bin_cmp': SQLOpBinCmp,
        'sql_op_bin_logic': SQLOpBinLogic,
        'sql_op_bin_op': SQLOpBinOp,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, op):
        self.op = op

    def __repr__(self):
        return '{}(op={})'.format(
            self.__class__.__name__,
            repr(self.op))

    def dump(self):
        return self.__repr__()


class SQLExprBinGeneral(AstNode):

    _clsmap = {
        'sql_op_bin': SQLOpBin,
        'sql_expr': SQLExpr,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        op, val = c
        # print('c', c)
        # print('op', op)
        # print('val', val)
        return cls(cls._clsmap[op.tag].from_parsetree(op),
                   cls._clsmap[val.tag].from_parsetree(val))

    def __init__(self, op, val):
        self.op = op
        self.val = val

    def __repr__(self):
        return '{}(op={}, val={})'.format(
            self.__class__.__name__,
            repr(self.op),
            repr(self.val))

    def dump(self):
        return self.__repr__()


class SQLOpBetween(AstNode):

    _clsmap = {
        'sql_expr_scalar': SQLExprScalar,
        'sql_value': SQLValue,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        print(c)
        _between = None
        left = None
        _and = None
        right = None
        _between, left, _and, right = c
        assert _between.str.lower() == 'between'
        assert _and.str.lower() == 'and'
        return cls(cls._clsmap[left.tag].from_parsetree(left),
                   cls._clsmap[right.tag].from_parsetree(right))

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return '{}(left={}, right={})'.format(
            self.__class__.__name__,
            repr(self.left),
            repr(self.right))

    def dump(self):
        return self.__repr__()


class SQLExprBinOpVal(AstNode):

    _clsmap = {
        'sql_expr_bin_general': SQLExprBinGeneral,
        'sql_op_between': SQLOpBetween,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.item))

    def dump(self):
        return self.__repr__()


class SQLExprName:

    _clsmap = {
        'sql_expr': SQLExpr,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.item))

    def dump(self):
        return self.__repr__()


class SQLSASExprName(AstNode):

    _clsmap = {
        'sql_expr_name': SQLExprName,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.item))

    def dump(self):
        return self.__repr__()


class SQLSASExprAliasItemNormal(AstNode):

    _clsmap = {
        'sql_sas_expr_name': SQLSASExprName,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.item))

    def dump(self):
        return self.__repr__()


class SQLSASExprAliasItemMacroPair(AstNode):

    _clsmap = {
        'macrovar': Macrovar,
        'sql_sas_expr_name': SQLSASExprName,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        # print('c.tag', c.tag)
        macrovar, expr = c
        return cls(cls._clsmap[macrovar.tag].from_parsetree(macrovar),
                   cls._clsmap[expr.tag].from_parsetree(expr))

    def __init__(self, macrovar, expr):
        self.macrovar = macrovar
        self.expr = expr

    def __repr__(self):
        return '{}(macrovar={}, expr={})'.format(
            self.__class__.__name__,
            repr(self.macrovar),
            repr(self.expr))

    def dump(self):
        return self.__repr__()


class SQLSASExprAliasItem(AstNode):

    _clsmap = {
        'sql_sas_expr_alias_item_normal': SQLSASExprAliasItemNormal,
        'sql_sas_expr_alias_item_macro_pair': SQLSASExprAliasItemMacroPair,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.item))

    def dump(self):
        return self.__repr__()


class SQLSASExprAliasNext(AstNode):
    pass


class SQLSASExprAliasList:

    _clsmap = {
        'sql_sas_expr_alias_item': SQLSASExprAliasItem,
        'sql_sas_expr_alias_next': SQLSASExprAliasNext,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.item))

    def dump(self):
        return self.__repr__()


class SQLStmtInto(AstNode):
    pass


class SQLExprAliasItem(AstNode):

    _clsmap = {
        'sql_expr_name': SQLExprName,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, aliases):
        self.aliases = aliases

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.aliases))

    def dump(self):
        return self.__repr__()


class SQLExprAliasList:

    _clsmap = {
        'sql_expr_alias_item': SQLExprAliasItem,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, aliases):
        self.aliases = aliases

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.aliases))

    def dump(self):
        return self.__repr__()


class SQLStmtFrom:

    _clsmap = {
        'sql_expr_alias_list': SQLExprAliasList,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        # print(c)
        _from, aliases = c
        assert _from.str.lower() == 'from'
        assert aliases.tag == 'sql_expr_alias_list'
        return cls(SQLExprAliasList.from_parsetree(aliases))

    def __init__(self, aliases):
        self.aliases = aliases

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.aliases))

    def dump(self):
        return self.__repr__()


class SQLJoinable(AstNode):

    _clsmap = {
        'sql_expr': SQLExpr,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c.tag', c.tag)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, aliases):
        self.aliases = aliases

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.aliases))

    def dump(self):
        return self.__repr__()


class SQLStmtJoinInner(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLStmtJoinLeftInner(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLStmtJoinRightInner(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLStmtJoinLeftOuter(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLStmtJoinRightOuter(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLStmtJoinFull(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLStmtJoinOuter(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLStmtJoinMod(AstNode):

    _map = {
        ('full', 'outer'):  SQLStmtJoinFull,
        ('full',):          SQLStmtJoinFull,
        ('inner',):         SQLStmtJoinLeftOuter,
        ('left', 'inner'):  SQLStmtJoinLeftInner,
        ('left', 'outer'):  SQLStmtJoinLeftOuter,
        ('left',):          SQLStmtJoinLeftInner,
        ('outer',):         SQLStmtJoinOuter,
        ('right', 'inner'): SQLStmtJoinRightInner,
        ('right', 'outer'): SQLStmtJoinRightOuter,
        ('right',):         SQLStmtJoinRightInner,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        k = tuple(s.str.lower() for s in c)
        return cls._map[k](pt)


class SQLStmtJoinUsing(AstNode):
    pass


class SQLStmtJoinOn:

    @classmethod
    def from_parsetree(cls, pt):

        c = pt.child
        # print('c', c)

        _on = None
        expr = None

        if c and c[0].tag == 'kwon':
            _on = c.pop(0)
            assert _on.str.lower() == 'on'
        if c and c[0].tag == 'sql_expr':
            expr = c.pop(0)
        assert not c

        return cls(SQLExpr.from_parsetree(expr))

    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return '{}(expr={})'.format(
            self.__class__.__name__,
            repr(self.expr))

    def dump(self):
        return self.__repr__()


class SQLStmtJoinCond(AstNode):

    _clsmap = {
        'sql_stmt_join_on': SQLStmtJoinOn,
        'sql_stmt_join_using': SQLStmtJoinUsing,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        # print('c', c)
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, aliases):
        self.aliases = aliases

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.aliases))

    def dump(self):
        return self.__repr__()


class SQLStmtJoin:

    _clsmap = {
        'sql_joinable': SQLJoinable,
    }

    @classmethod
    def from_parsetree(cls, pt):

        c = pt.child
        # print('c', c)

        mod = None
        _join = None
        joinable = None
        cond = None

        if c and c[0].tag == 'sql_stmt_join_mod':
            mod = c.pop(0)
        if c and c[0].tag == 'kwjoin':
            _join = c.pop(0)
            assert _join.str.lower() == 'join'
        if c and c[0].tag == 'sql_joinable':
            joinable = c.pop(0)
        if c and c[0].tag == 'sql_stmt_join_cond':
            cond = c.pop(0)

        return cls(SQLStmtJoinMod.from_parsetree(mod) if mod else None,
                   SQLJoinable.from_parsetree(joinable) if joinable else None,
                   SQLStmtJoinCond.from_parsetree(cond) if cond else None)

    def __init__(self, mod, joinable, cond):
        self.mod = mod
        self.joinable = joinable
        self.cond = cond

    def __repr__(self):
        return '{}(mod={}, joinable={}, cond={})'.format(
            self.__class__.__name__,
            repr(self.mod),
            repr(self.joinable),
            repr(self.cond))

    def dump(self):
        return self.__repr__()


class SQLStmtJoinList(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        if pt is None:
            return None
        # print('pt', pt)
        c = pt.child
        return cls(map(SQLStmtJoin.from_parsetree, c))

    def __init__(self, joins):
        self.joins = list(joins)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.joins))

    def dump(self):
        return self.__repr__()


class SQLStmtWhere(AstNode):

    @classmethod
    def from_parsetree(cls, pt):

        if pt is None:
            return None

        c = pt.child
        # print('c', c)

        _where = None
        expr = None

        if c and c[0].tag == 'kwwhere':
            _where = c.pop(0)
            assert _where.str.lower() == 'where'
        if c and c[0].tag == 'sql_expr':
            expr = c.pop(0)
        assert not c

        return cls(SQLExpr.from_parsetree(expr))

    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return '{}(expr={})'.format(
            self.__class__.__name__,
            repr(self.expr))

    def dump(self):
        return self.__repr__()


class SQLStmtGroupby:

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        # print(c)
        _group, _by, expr_list = c
        assert _group.str.lower() == 'group'
        assert _by.str.lower() == 'by'
        assert expr_list.tag == 'sql_expr_list'
        return cls(SQLExprList.from_parsetree(expr_list))

    def __init__(self, expr_list):
        self.expr_list = expr_list

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.expr_list))

    def dump(self):
        return self.__repr__()


class SQLStmtHaving(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        print(c)
        _having = None
        expr = None
        _having, expr = c
        assert _having.str.lower() == 'having'
        return cls(SQLExpr.from_parsetree(expr))

    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return '{}(expr={})'.format(
            self.__class__.__name__,
            repr(self.expr))

    def dump(self):
        return self.__repr__()


class SQLStmtOrderbyExpr(AstNode):
    pass


class SQLStmtOrderbyList(AstNode):
    pass


class SQLStmtOrderby(AstNode):

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child
        print(c)
        _order = None
        _by = None
        expr_list = None
        if len(c) == 3:
            _order, _by, expr_list = c
            assert _order.str.lower() == 'order'
            assert _by.str.lower() == 'by'
            assert expr_list.tag == 'sql_stmt_orderby_list'
        elif len(c) == 2:
            _order, expr_list = c
            assert _order.str.lower() == 'order'
            assert expr_list.tag == 'sql_stmt_orderby_list'
        else:
            raise NotImplementedError(c)
        return cls(SQLExprList.from_parsetree(expr_list))

    def __init__(self, expr_list):
        self.expr_list = expr_list

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.expr_list))

    def dump(self):
        return self.__repr__()


class SQLSASSetOpExcept(AstNode):

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLSASSetOpIntersect(AstNode):

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLSASSetOpUnion(AstNode):

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLSASSetOpUnionOuter(AstNode):

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class SQLSASSetOp(AstNode):

    _clsmap = {
        'sql_sas_set_except': SQLSASSetOpExcept,
        'sql_sas_set_intersect': SQLSASSetOpIntersect,
        'sql_sas_set_union': SQLSASSetOpUnion,
        'sql_sas_set_union_outer': SQLSASSetOpUnionOuter,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, query):
        self.query = query

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.query))

    def dump(self):
        return self.__repr__()


class SQLStmtSet(AstNode):

    _clsmap = {
        'sql_sas_set_op': SQLSASSetOp,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, setop):
        self.setop = setop

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.setop))

    def dump(self):
        return self.__repr__()


class SQLExprSelect(AstNode):

    @classmethod
    def from_parsetree(cls, pt):

        c = pt.child
        # print('c', c)

        _select = None
        exprs = None
        intos = None
        froms = None
        joins = None
        wheres = None
        groupbys = None
        havings = None
        orderbys = None
        sets = None

        _select = c.pop(0)
        assert _select.str.lower() == 'select'
        if c and c[0].tag == 'sql_sas_expr_alias_list':
            exprs = c.pop(0)
        if c and c[0].tag == 'sql_stmt_into':
            intos = c.pop(0)
        if c and c[0].tag == 'sql_stmt_from':
            froms = c.pop(0)
        if c and c[0].tag == 'sql_stmt_join_list':
            joins = c.pop(0)
        if c and c[0].tag == 'sql_stmt_where':
            wheres = c.pop(0)
        if c and c[0].tag == 'sql_stmt_groupby':
            groupbys = c.pop(0)
        if c and c[0].tag == 'sql_stmt_having':
            havings = c.pop(0)
        if c and c[0].tag == 'sql_stmt_orderby':
            orderbys = c.pop(0)
        if c and c[0].tag == 'sql_stmt_set':
            sets = c.pop(0)

        if c:
            print('c', c)
        assert not c

        return cls(SQLSASExprAliasList.from_parsetree(exprs) if exprs else None,
                   SQLStmtInto.from_parsetree(intos) if intos else None,
                   SQLStmtFrom.from_parsetree(froms) if froms else None,
                   SQLStmtJoinList.from_parsetree(joins) if joins else None,
                   SQLStmtWhere.from_parsetree(wheres) if wheres else None,
                   SQLStmtGroupby.from_parsetree(groupbys) if groupbys else None,
                   SQLStmtHaving.from_parsetree(havings) if havings else None,
                   SQLStmtOrderby.from_parsetree(orderbys) if orderbys else None,
                   SQLStmtSet.from_parsetree(sets) if sets else None)

    def __init__(self,
                 exprs,
                 intos,
                 froms,
                 joins,
                 where,
                 groupbys,
                 havings,
                 orderbys,
                 sets):
        self.exprs = exprs
        self.intos = intos
        self.froms = froms
        self.joins = joins
        self.where = where
        self.groupbys = groupbys
        self.havings = havings
        self.orderbys = orderbys
        self.sets = sets

    def __repr__(self):
        return '{}(expr={}, into={}, from={}, join={}, where={}, groupby={}, having={}, orderby={}, set={})'.format(
            self.__class__.__name__,
            repr(self.exprs),
            repr(self.intos),
            repr(self.froms),
            repr(self.joins),
            repr(self.where),
            repr(self.groupbys),
            repr(self.havings),
            repr(self.orderbys),
            repr(self.sets))

    def dump(self):
        return self.__repr__()

SQLQuerySelect._clsmap['sql_expr_select'] = SQLExprSelect


class SQLExprSelectParens:

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        return cls(SQLExprSelect.from_parsetree(c))

    def __init__(self, query):
        self.query = query

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.query))

    def dump(self):
        return self.__repr__()


class SQLExprCreateTableAs(SymIO):

    _clsmap = {
        'sql_expr_select': SQLExprSelect,
        'sql_stmt_select_parens': SQLExprSelectParens,
    }

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0]
        return cls(cls._clsmap[c.tag].from_parsetree(c))

    def __init__(self, query):
        self.query = query

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.query))

    def dump(self):
        return self.__repr__()


class SQLStmtCreateTable(SymIO):

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.child[0].child
        # print('c', c)
        _create, _table, tablename = c[0:3]
        assert _create.str.lower() == 'create'
        assert _table.str.lower() == 'table'
        del c[0:3]
        filter_expr = None
        as_expr = None
        if c[0].tag == 'sas_sql_create_table_expr':
            filter_expr = c.pop(0)
        if c[0].str.lower() == 'as':
            c.pop(0)
        if c[0].tag == 'sql_expr_create_table_as':
            as_expr = c.pop(0)
        assert not c
        return cls(tablename,
                   filter_expr,
                   SQLExprCreateTableAs.from_parsetree(as_expr))

    def __init__(self, tablename, filter_expr, as_expr):
        self.tablename = tablename
        self.filter_expr = filter_expr
        self.as_expr = as_expr

    def __repr__(self):
        return '{}(in={}, out={}, tablename={}, filter_expr={}, as_expr={})'.format(
            self.__class__.__name__,
            self.symbols_in(),
            self.symbols_out(),
            repr(self.tablename),
            repr(self.filter_expr),
            self.as_expr.dump())

    def symbols_in(self):
        return []  # self.as_expr.symbols_in()

    def symbols_out(self):
        return [self.tablename]


class ProcSQLBodyStmt(SymIO):

    _clsmap = {
        'sql_stmt_create_table': SQLStmtCreateTable,
    }

    @classmethod
    def from_parsetree(cls, pt):
        if not pt.child or not pt.str.strip():
            return None
        ch = pt.child[0]
        cl = cls._clsmap.get(ch.tag)
        return cls(cl.from_parsetree(ch) if cl else ch)

    def __init__(self, sets):
        self.sets = sets

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               repr(self.sets))

    def symbols_in(self):
        symbols = []
        if isinstance(self.sets, SymIO):
            symbols.extend(self.sets.symbols_in())
        return symbols

    def symbols_out(self):
        return []


class ProcSQLOpts(AstNode):
    pass


class ProcSQLBody(SymIO):

    @classmethod
    def from_parsetree(cls, pt):
        return cls(map(ProcSQLBodyStmt.from_parsetree, pt.child))

    def __init__(self, stmts):
        self.stmts = [s for s in stmts if s]

    def __iter__(self):
        return iter(self.stmts)

    def symbols_in(self):
        symbols = []
        for stmt in self.stmts:
            if isinstance(stmt, SymIO):
                symbols.extend(stmt.symbols_in())
        return symbols

    def symbols_out(self):
        return []

    def __repr__(self):
        return '{}(stmts={})'.format(self.__class__.__name__,
                                     repr(self.stmts))


class ProcSQLStmt(AstNode):  # TODO: SymIO

    @classmethod
    def from_parsetree(cls, pt):
        c = pt.filterspace().child
        # print(c)
        # _proc, _sql = c[:2]
        rest = c[2:]
        opts = None
        body = None
        if rest[0].tag == 'proc_sql_opts':
            opts = rest.pop(0)
        if rest[0].tag == 'proc_sql_body':
            body = rest.pop(0)
            # print('body', body)
        assert not rest
        return cls(ProcSQLOpts.from_parsetree(opts),
                   ProcSQLBody.from_parsetree(body))

    def __init__(self, opts, body):
        self.opts = opts
        # print('body', body)
        # self.body = body.filter(lambda node: not not node.str.strip())
        # self.stmts = [x for x in [ch.str.strip() for ch in body.child] if x]
        self.body = body

    def __repr__(self):
        return '{}:\n{}'.format(self.__class__.__name__,
                                self.body)

    def symbols_in(self):
        raise NotImplementedError

    def symbols_out(self):
        raise NotImplementedError


class ProcTemplateStmt(AstNode):
    pass


class ProcTransposeStmt(AstNode):
    pass


class ProcUnivariateStmt(AstNode):
    pass


ProcStmt._clsmap = {
    'proc_catalog': ProcCatalogStmt,
    'proc_cimport': ProcCImportStmt,
    'proc_contents': ProcContentsStmt,
    'proc_corr': ProcCorrStmt,
    'proc_datasets': ProcDatasetsStmt,
    'proc_export': ProcExportStmt,
    'proc_format': ProcFormatStmt,
    'proc_freq': ProcFreqStmt,
    'proc_gmap': ProcGmapStmt,
    'proc_gremove': ProcGremoveStmt,
    'proc_import': ProcImportStmt,
    'proc_means': ProcMeansStmt,
    'proc_options': ProcOptionsStmt,
    'proc_print': ProcPrintStmt,
    'proc_pwencode': ProcPwEncodeStmt,
    'proc_rank': ProcRankStmt,
    'proc_report': ProcReportStmt,
    'proc_sgpanel': ProcSGPanelStmt,
    'proc_sgplot': ProcSGPlotStmt,
    'proc_sort': ProcSortStmt,
    'proc_sql': ProcSQLStmt,
    'proc_template': ProcTemplateStmt,
    'proc_transpose': ProcTransposeStmt,
    'proc_univariate': ProcUnivariateStmt,
}


class OdsStmt(AstNode):
    pass


class DoStmt(AstNode):
    pass


class DoOverStmt(AstNode):
    pass


class DoToStmt(AstNode):
    pass


class DoUntilStmt(AstNode):
    pass


class PreProcStmt(AstNode):
    pass


class RunStmt(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class QuitStmt(AstNode):
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class PutStmt(AstNode):
    pass


class SignOnStmt(AstNode):
    pass


class VarStmt(AstNode):
    pass


class DropStmt(AstNode):
    pass


class FuncesqueOpStmt(AstNode):
    pass


class TopLevel:

    @classmethod
    def from_parsetree(cls, pt):
        c = cls._clsmap.get(pt.tag)
        if c:
            return c.from_parsetree(pt)
        elif pt.tag not in cls._clsmap:
            if pt.tag == 'toplevel':
                return cls.from_parsetree(pt.child[0])
            raise NotImplementedError(pt.tag)
        return None

    _clsmap = {
        'assign_stmt': AssignStmt,
        'array_stmt': ArrayStmt,
        'comment': Comment,
        'data_stmt': DataStmt,
        'datalines_stmt': DatalinesStmt,
        'do_stmt': DoStmt,
        'do_to_stmt': DoToStmt,
        'do_over_stmt': DoOverStmt,
        'do_until_stmt': DoUntilStmt,
        'drop_stmt': DropStmt,
        'else_stmt': ElseStmt,
        'empty_stmt': EmptyStmt,
        'expr_stmt': ExprStmt,
        'filename_stmt': FilenameStmt,
        'footnote_stmt': Footnote,
        'format_stmt': FormatStmt,
        'if_stmt': IfStmt,
        'input_stmt': InputStmt,
        'length_stmt': LengthStmt,
        'libname_stmt': LibnameStmt,
        'macro': Macro,
        'toplevel_funcesque_op': FuncesqueOpStmt,
        'preproc_stmt': PreProcStmt,
        'ods_stmt': OdsStmt,
        'options_stmt': Options,
        'pattern_stmt': Pattern,
        'proc_stmt': ProcStmt,
        'put_stmt': PutStmt,
        'quit_stmt': QuitStmt,
        'run_stmt': RunStmt,
        'sas_expr': SASExpr,
        'signon_stmt': SignOnStmt,
        'space': None,  # Space,
        'title_stmt': Title,
        'var_stmt': VarStmt,
    }

# now that TopLevel is defined, connect it to _clsmap which can receive 'toplevel'
DataBodyStmt._clsmap['toplevel'] = TopLevel
