#!/usr/bin/env python

# CAVEAT UTILITOR
#
# This file was automatically generated by Grako.
#
#    https://pypi.python.org/pypi/grako/
#
# Any changes you make to it will be overwritten the next time
# the file is generated.
from grako.buffering import Buffer
from grako.parsing import graken, Parser
from grako.util import generic_main  # noqa

KEYWORDS = {}


class DisplayPatternBuffer(Buffer):
    def __init__(
            self,
            text,
            whitespace=None,
            nameguard=None,
            comments_re=None,
            eol_comments_re=None,
            ignorecase=None,
            namechars='',
            **kwargs
    ):
        super(DisplayPatternBuffer, self).__init__(
            text,
            whitespace=whitespace,
            nameguard=nameguard,
            comments_re=comments_re,
            eol_comments_re=eol_comments_re,
            ignorecase=ignorecase,
            namechars=namechars,
            **kwargs
        )


class DisplayPatternParser(Parser):
    def __init__(
            self,
            whitespace=None,
            nameguard=None,
            comments_re=None,
            eol_comments_re=None,
            ignorecase=None,
            left_recursion=False,
            parseinfo=True,
            keywords=None,
            namechars='',
            buffer_class=DisplayPatternBuffer,
            **kwargs
    ):
        if keywords is None:
            keywords = KEYWORDS
        super(DisplayPatternParser, self).__init__(
            whitespace=whitespace,
            nameguard=nameguard,
            comments_re=comments_re,
            eol_comments_re=eol_comments_re,
            ignorecase=ignorecase,
            left_recursion=left_recursion,
            parseinfo=parseinfo,
            keywords=keywords,
            namechars=namechars,
            buffer_class=buffer_class,
            **kwargs
        )

    @graken()
    def _start_(self):
        self._pattern_()
        self._check_eof()

    @graken()
    def _pattern_(self):
        def block0():
            with self._choice():
                with self._option():
                    self._text_()
                with self._option():
                    self._tag_()
                with self._option():
                    self._function_()
                self._error('no available options')

        self._closure(block0)

    @graken()
    def _tag_(self):
        with self._group():
            self._token('%')
            self._string_()
            self.name_last_node('name')

            def block2():
                self._token(',')
                with self._group():
                    self._parameter_()
                self.add_last_node_to_name('parameters')

            self._closure(block2)
            self._token('%')
        self.name_last_node('tag')
        self.ast._define(
            ['name', 'tag'],
            ['parameters']
        )

    @graken()
    def _function_(self):
        with self._group():
            self._token('$')
            self._string_()
            self.name_last_node('name')
            self._token('(')
            with self._optional():
                with self._group():
                    self._parameter_()
                self.add_last_node_to_name('parameters')

                def block3():
                    self._token(',')
                    with self._group():
                        self._parameter_()
                    self.add_last_node_to_name('parameters')

                self._closure(block3)
            self._token(')')
        self.name_last_node('function')
        self.ast._define(
            ['function', 'name'],
            ['parameters']
        )

    @graken()
    def _parameter_(self):
        with self._optional():
            def block0():
                self._token(' ')

            self._closure(block0)
            self._string_()
            self.name_last_node('name')
            self._token('=')
        with self._optional():
            self._pattern_()
            self.name_last_node('value')
        self.ast._define(
            ['name', 'value'],
            []
        )

    @graken()
    def _text_(self):
        self._pattern(r'(\\\\|\\%|\\\$|\\,|\\\(|\\\)|\\=|\\n|\\t|[^\\%$,()])+')
        self.name_last_node('text')
        self.ast._define(
            ['text'],
            []
        )

    @graken()
    def _string_(self):
        self._pattern(r'([^\\%$,()=])+')


class DisplayPatternSemantics(object):
    def start(self, ast):
        return ast

    def pattern(self, ast):
        return ast

    def tag(self, ast):
        return ast

    def function(self, ast):
        return ast

    def parameter(self, ast):
        return ast

    def text(self, ast):
        return ast

    def string(self, ast):
        return ast


def main(filename, startrule, **kwargs):
    with open(filename) as f:
        text = f.read()
    parser = DisplayPatternParser()
    return parser.parse(text, startrule, filename=filename, **kwargs)


if __name__ == '__main__':
    import json
    from grako.util import asjson

    ast = generic_main(main, DisplayPatternParser, name='DisplayPattern')
    print('AST:')
    print(ast)
    print()
    print('JSON:')
    print(json.dumps(asjson(ast), indent=2))
    print()
