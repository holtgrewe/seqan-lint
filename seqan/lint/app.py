#!/usr/bin/env python

from __future__ import print_function

import argparse
import os.path
import fnmatch
import re
import sys


class SourceLocation(object):
    def __init__(self, filename, line, column):
        self.filename = filename
        self.line = line
        self.column = column


class Issue(object):
    def __init__(self, location, text='', level='warning'):
        self.location = location
        self.text = text
        self.level = level


Issue.WARNING = 'warning'
Issue.ERROR = 'error'


class Checker(object):
    def __init__(self):
        self.name = None

    def run(self, fname, fcontents):
        """
        @param fname     path to the file
        @param fcontents file contents

        @returns list of Issue
        """
        return []


class FileEndsWithNewline(Checker):
    def __init__(self):
        self.name = 'trailing_whitespace'

    def run(self, fname, fcontents):
        if fcontents and not fcontents[-1] == '\n':
            lines = fcontents.splitlines(False)
            line = len(lines)
            col = len(lines[-1])
            return [Issue(SourceLocation(fname, line, col),
                          'File does not end with newline.')]
        return []
            


class TrailingWhitespace(Checker):
    def __init__(self):
        self.name = 'file_ends_with_newline'

    def run(self, fname, fcontents):
        result = []
        for lineno, line in enumerate(fcontents.splitlines(False)):
            if line and line[-1].isspace():
                col = re.search('\s+$', line).start(0) + 1
                result.append(Issue(SourceLocation(fname, lineno + 1, col),
                              'Trailing whitespace in this line.'))
        return result                

CHECKERS = [FileEndsWithNewline(), TrailingWhitespace()]


class LintConf(object):
    def __init__(self, patterns=[], checkers=[]):
        self.patterns = list(patterns)
        self.checkers = self._checkers(checkers)

    def _checkers(self, checkers):
        """Return checkers."""
        return [c for c in CHECKERS if c.name in set(checkers)]

    def run(self, path):
        result = []
        with open(path, 'rb') as f:
            fcontents = f.read()
            result += self.runWithContents(path, fcontents)
        return result

    def runWithContents(self, path, fcontents):
        result = []
        for checker in self.checkers:
            result += checker.run(path, fcontents)
        return result


def buildConf():
    result = []
    result.append(LintConf(['*.cpp', '*.h'], checkers=[
                'trailing_whitespace',
                'file_ends_with_newline',
                ]))
    result.append(LintConf(['README*', '.txt'], checkers=[
                'trailing_whitespace',
                'file_ends_with_newline',
                ]))
    return result


class IssuePrinter(object):
    def show(self, issue):
        print('%s (%s): %s' % (self.fmtLoc(issue.location), issue.level, issue.text),
              file=sys.stderr)

    def fmtLoc(self, sloc):
        return '%s:%d:%d' % (os.path.basename(sloc.filename), sloc.line, sloc.column)


def printIssues(issues):
    printer = IssuePrinter()
    for issue in issues:
        printer.show(issue)
    print('Total Issues: %d' % len(issues), file=sys.stderr)


def run(conf, files):
    results = []
    for path in files:
        for c in conf:
            for pat in c.patterns:
                if not fnmatch.fnmatch(os.path.basename(path), pat):
                    continue  # Skip
                results += c.run(path)
    printIssues(results)


def main():
    parser = argparse.ArgumentParser(description='Perform checks on source code.')

    parser.add_argument('-f', '--file', dest='files', action='append',
                        help='The file to check.', default=[])
    args = parser.parse_args()
    return run(buildConf(), args.files)


if __name__ == '__main__':
    sys.exit(main())
