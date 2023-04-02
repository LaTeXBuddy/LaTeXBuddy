# Authoring a change

After you've [set up the environment](./environment.md), you can clone the repo
and start working on the issue.

## Branch rules

LaTeXBuddy follows to the
‘[Trunk Based Development](https://trunkbaseddevelopment.com/)’ branching model.
The trunk branch is called `master` and always contains a known-bug-free and
correctly executable version of the software.

No commits may be pushed directly to the trunk branch (in other words, the trunk
branch is protected); instead, changes are merged into `master` using merge
requests.

For each individual feature or bugfix, a short-lived branch, which is (usually)
edited by one person and reviewed by several additional people, should be
created. Name the branch with the short summary of planned changes in
`camel-case`. If the work on the branch is intended to fix a specific issue, prepend the name
with the issue number. For example: `119-fix-html-output`.

After the feature is completed and tested, the corresponding branch is
merged with the trunk branch and then deleted — this is done automatically with
the closing of the merge request. Merge Requests for the `master` branch have
to be approved by a maintainer.

## Log your changes

To track the changes, we use [towncrier](https://towncrier.readthedocs.io/en/stable/index.html). Instead of writing all changes to a big CHANGELOG file, we propose you author the changelog entries as small file snippets.

After you have implemented a change, create a file under `changelog.d/` with the name of `<ISSUE_NUMBER>.<CATEGORY>.md`, where `<ISSUE_NUMBER>` is the number of the issue you're closing with your change, and `<CATEGORY>` is one of: `breaking`, `add`, `change`, `fix`, `remove`, `deprecate`, `internal`. If you don't have an issue number (for example, you directly proposed a pull request), use some unique ID with a `+` sign prepended.

For example, this is the changelog entry for introducing towncrier, stored in the file `+towncrier.internal.md`:

```md
Towncrier is now used to generate the changelog
```

## Commit guidelines

### What is a commit

A commit should contain a coherent set of changes within it. Commits should be
‘atomic’ — that means, they should add/remove/fix only one thing. This does not
mean that each commit changes only one line. Consideration should be given to
what would happen if the commit were to be reverted, rebased, or rearranged.

Once pushed, commits **may not** be overwritten (e.g. force-pushed); if a change
needs to be reverted, a new commit must be created. The only exception to that
rule would take place if sensitive data was pushed, like a password or an auth
token.

### Commit message

Each commit must have a clear, descriptive message. The message should be
written in English (preferably British) and phrased imperatively. The first word
should be capitalized. In other words, the commit message should finish the
phrase ‘If I apply this commit, it will…’. A good commit message would be:
`Fix the spellchecking bug`. The commit message should remain as short as
possible and, if possibly, not exceed 50 characters in length.

If one line is not enough to describe the changes the commit introduces,
additional information can be added in the commit’s description. For example, if
a commit is related to an issue and/or merge request, the issue or merge request
number could appear in the description. If the commit implements or resolves an
issue, the issue number should be prefixed with the word ‘Closes’.

Example of a commit that fixes a bug with the issue described in Issue #5, and
(perhaps) also a bug from Issue #8:

```
Fix incorrect output of spellcheck errors

Closes #5
This may also fix the incorrect output for chktex-related errors (see #8)
```
