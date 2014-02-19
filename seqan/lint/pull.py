#!/usr/bin/env python

import argparse
import base64
import json
import sys

import github
import unidiff
import requests

import app

# For testing getNewLines
DIFF="""@@ -2,7 +2,8 @@

 # get some infos from git to embed it in the build name
 export SOURCE_DIRECTORY=`pwd`
-mkdir _build
+mkdir -p _build
+mkdir foo

 # define the build name
 if [ "${TRAVIS_PULL_REQUEST}" != "false" ]; then
@@ -12,7 +12,8 @@

 # get some infos from git to embed it in the build name
 export SOURCE_DIRECTORY=`pwd`
-mkdir _build
+mkdir -p _build
+mkdir foo

 # define the build name
 if [ "${TRAVIS_PULL_REQUEST}" != "false" ]; then
"""


def getNewLines(unified_diff):
    """Parse out the lines that are new in the file the diff is for."""
    result = []
    from_offset, from_count, to_offset, to_count = 0, 0, 0, 0
    relno = 0  # relative line no
    for line in unified_diff.splitlines(False):
        if line.startswith('@@') and line.endswith('@@'):
            from_, to_ = line.split()[1:3]
            assert from_.startswith('-')
            assert to_.startswith('+')
            from_offset, from_count = map(int, from_[1:].split(','))
            to_offset, to_count = map(int, to_[1:].split(','))
            relno = to_offset - 1
        if line.startswith('+'):
            result.append(relno)
        if not line.startswith('-'):
            relno += 1
    return result


def run(repo_name, pull_request, token=None):
    conf = app.buildConf()
    print 'Running for repository %s pull request #%d' % (repo_name, pull_request)
    g = github.Github('holtgrewe', token)
    print 'Getting repository %s' % repo_name
    repo = g.get_repo(repo_name)
    print 'Getting pull request #%d' % pull_request
    pull = repo.get_pull(pull_request)
    print '  Pull request at: %s' % pull.html_url
    print 'Getting files...'
    files = pull.get_files()
    all_issues = []
    for f in files:
        print '  %s' % f.filename
        print '    status:   %s' % f.status
        print '    raw:      %s' % f.raw_url
        print '    blob:     %s' % f.blob_url
        #print '    contents: %s' % f.contents_url
        #print '    patch:    %s' % f.patch
        print '    new lines: %s' % getNewLines(f.patch)
        newLines = set(getNewLines(f.patch))
        if not newLines:
            continue
        r = requests.get(f.contents_url, auth=('holtgrewe', token))
        if r.status_code != 200:
            raise Exception('Problem retrieving contents: %s' % r.text)
        j = json.loads(r.text)
        fcontents = base64.b64decode(j['content'])
        # Collect issues and filter for new lines.
        issues = sum((c.runWithContents(f.filename, fcontents) for c in conf), [])
        issues = [issue for issue in issues if issue.location.line in newLines]
        all_issues += issues
    app.printIssues(all_issues)


def main():
    parser = argparse.ArgumentParser(description='Perform checks on source code.')

    parser.add_argument('-r', '--repository', dest='repository', required=True,
                        help='The repository to query.')
    parser.add_argument('-p', '--pull-request', dest='pull_request', required=True,
                        help='The pull request to check.', type=int)
    parser.add_argument('-t', '--token', dest='token', default=None,
                        help='The token to use.', type=str)
    parser.add_argument('--debug', dest='debug', default=False, action='store_true')
    args = parser.parse_args()
    if args.debug:
        github.enable_console_debug_logging()
    return run(args.repository, args.pull_request, args.token)


if __name__ == '__main__':
    #print getNewLines(DIFF)
    sys.exit(main())
