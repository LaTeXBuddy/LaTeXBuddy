# Authoring a change

## Log your Changes

To track the changes, we use [towncrier](https://towncrier.readthedocs.io/en/stable/index.html). Instead of writing all changes to a big CHANGELOG file, we propose you author the changelog entries as small file snippets.

After you have implemented a change, create a file under `changelog.d/` with the name of `<ISSUE_NUMBER>.<CATEGORY>.md`, where `<ISSUE_NUMBER>` is the number of the issue you're closing with your change, and `<CATEGORY>` is one of: `breaking`, `add`, `change`, `fix`, `remove`, `deprecate`, `internal`. If you don't have an issue number (for example, you directly proposed a pull request), use some unique ID with a `+` sign prepended.

For example, this is the changelog entry for introducing towncrier, stored in the file `+towncrier.internal.md`:

```md
Towncrier is now used to generate the changelog
```
