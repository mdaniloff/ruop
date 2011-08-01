# -*- coding: utf-8 -*-

import traceback

from .utils import format_kwargs
from .tokenize import Token
from .config import SOURCE_EXPRESSION_MARKER_LENGTH as LENGTH


def compute_source_marker(line, column, expression, size):
    """Computes source marker location string.

    >>> def test(l, c, e, s):
    ...     s, marker = compute_source_marker(l, c, e, s)
    ...     out = s + '\\n' + marker
    ...
    ...     # Replace dot with middle-dot to work around doctest ellipsis
    ...     print(out.replace('...', '···'))

    >>> test('foo bar', 4, 'bar', 7)
    foo bar
        ^^^

    >>> test('foo ${bar}', 4, 'bar', 10)
    foo ${bar}
          ^^^

    >>> test('  foo bar', 6, 'bar', 6)
    ··· oo bar
           ^^^

    >>> test('  foo bar baz  ', 6, 'bar', 6)
    ··· o bar ···
          ^^^

    The entire expression is always shown, even if ``size`` does not
    accomodate for it.

    >>> test('  foo bar baz  ', 6, 'bar baz', 10)
    ··· oo bar baz
           ^^^^^^^

    >>> test('      foo bar', 10, 'bar', 5)
    ··· o bar
          ^^^

    >>> test('      foo bar', 10, 'boo', 5)
    ··· o bar
          ^

    """

    s = line.lstrip()
    column -= len(line) - len(s)
    s = s.rstrip()

    try:
        i  = s[column:].index(expression)
    except ValueError:
        # If we can't find the expression
        # (this shouldn't happen), simply
        # use a standard size marker
        marker = "^"
    else:
        column += i
        marker = "^" * len(expression)

    if len(expression) > size:
        offset = column
        size = len(expression)
    else:
        window = (size - len(expression)) / 2.0
        offset = column - window
        offset -= min(3, max(0, column + window + len(expression) - len(s)))
        offset = int(offset)

    if offset > 0:
        s = s[offset:]
        r = s.lstrip()
        d = len(s) - len(r)
        s = "... " + r
        column += 4 - d
        column -= offset

        # This also adds to the displayed length
        size += 4

    if len(s) > size:
        s = s[:size].rstrip() + " ..."

    return s, column * " " + marker


class TemplateError(Exception):
    def __init__(self, msg, token):
        if not isinstance(token, Token):
            token = Token(token, 0)

        self.msg = msg
        self.token = token
        self.filename = token.filename

    def __str__(self):
        text = "%s\n\n" % self.msg
        text += "   - String:   \"%s\"" % self.token

        if self.filename:
            text += "\n"
            text += "   - Filename: %s" % self.filename

        try:
            line, column = self.token.location
        except AttributeError:
            pass
        else:
            text += "\n"
            text += "   - Location: (%d:%d)" % (line, column)

        return text

    def __repr__(self):
        try:
            return "%s(%r, %r)" % (
                self.__class__.__name__, self.msg, self.token
                )
        except AttributeError:
            return object.__repr__(self)

    @property
    def offset(self):
        return getattr(self.token, "pos", 0)


class ParseError(TemplateError):
    """An error occurred during parsing.

    Indicates an error on the structural level.
    """


class CompilationError(TemplateError):
    """An error occurred during compilation.

    Indicates a general compilation error.
    """


class TranslationError(TemplateError):
    """An error occurred during translation.

    Indicates a general translation error.
    """


class LanguageError(CompilationError):
    """Language syntax error.

    Indicates a syntactical error due to incorrect usage of the
    template language.
    """


class ExpressionError(LanguageError):
    """An error occurred compiling an expression.

    Indicates a syntactical error in an expression.
    """


class ExceptionFormatter(object):
    def __init__(self, errors, econtext, rcontext):
        kwargs = rcontext.copy()
        kwargs.update(econtext)

        for name in tuple(kwargs):
            if name.startswith('__'):
                del kwargs[name]

        self._errors = errors
        self._kwargs = kwargs

    def __call__(self):
        # Format keyword arguments; consecutive arguments are indented
        # for readability
        try:
            formatted = format_kwargs(self._kwargs)
        except:
            # the ``pprint.pformat`` method calls the representation
            # method of the arguments; this may fail and since we're
            # already in an exception handler, there's no point in
            # pursuing this further
            formatted = ()

        for index, string in enumerate(formatted[1:]):
            formatted[index + 1] = " " * 15 + string

        out = []

        for error in self._errors:
            expression, line, column, filename, exc = error
            out.append(" - Expression: \"%s\"" % expression)
            out.append(" - Filename:   %s" % (filename or "<string>"))
            out.append(" - Location:   (%d:%d)" % (line, column))

            if filename and line and column:
                try:
                    f = open(filename, 'r')
                except IOError:
                    pass
                else:
                    try:
                        # Pick out source line and format marker
                        for i, l in enumerate(f):
                            if i + 1 == line:
                                s, marker = compute_source_marker(
                                    l, column, expression, LENGTH
                                    )

                                out.append("")
                                out.append(" - Source:     %s" % s)
                                out.append("               %s" % marker)
                                break
                    finally:
                        f.close()

        out.append(" - Arguments:  %s" % "\n".join(formatted))

        formatted_exc = traceback.format_exception_only(type(exc), exc)[-1]
        formatted_exc_class = "%s:" % type(exc).__name__
        if formatted_exc.startswith(formatted_exc_class):
            formatted_exc = formatted_exc[len(formatted_exc_class):].lstrip()

        return "\n".join([formatted_exc] + out)