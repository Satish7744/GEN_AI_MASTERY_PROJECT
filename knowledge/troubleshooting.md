# Linux and Git troubleshooting guide

Use this guide as a starting point, not as a substitute for the exact error output.
Ask which operating system, shell, command, and goal apply when that information is
missing. Ask users to remove passwords, API keys, access tokens, and private URLs before
sharing terminal output.

## A safe troubleshooting sequence

1. Read the complete error and identify the command or program that produced it.
2. Confirm the operating system and shell. Linux shell commands are not interchangeable
   with Windows PowerShell or Command Prompt commands.
3. Start with read-only checks such as `pwd`, `ls -la`, `git status`, or a tool's
   `--version` option when relevant.
4. Explain the likely cause, then suggest one small change at a time.
5. Ask the user to rerun the command and share the new output if the problem remains.

Do not start with `sudo`, broad permission changes such as `chmod -R 777`, destructive
file operations, `git reset --hard`, or commands that rewrite shared Git history.
Inspect the working tree and explain data-loss risks before suggesting a Git undo.

## Common Linux errors

### `command not found`

The shell cannot find a program with that name. Check spelling, then inspect whether it
is installed and on `PATH` with `command -v program-name` and `printf '%s\n' "$PATH"`.
Installation steps depend on the Linux distribution; identify it before suggesting a
package-manager command.

### `Permission denied`

The current user may lack permission to read, write, or execute the target. Inspect the
path and permissions with `pwd`, `ls -ld path`, `ls -l path`, and `id`. Check directory
permissions along the full path. Do not recommend `chmod -R 777`; use the narrowest
permission change that matches the user's intended access, and explain the effect.

### `No space left on device`

Check filesystem capacity with `df -h` and inode availability with `df -i`. Identify
large files before deleting anything. Do not recommend deleting system or application
data without confirming what it is and whether it is needed.

## Common Git errors

### Normal `git status` output

`git status` may report modified files and untracked files without any error. This is
informational: it shows working-tree changes. Use `git diff` to inspect tracked edits
and `git status --short` for a compact summary. If useful, mention that the user may
open an untracked file in an editor to inspect it; `git diff` does not show its
contents. If offering staging, show only the template `git add <chosen-file>` and tell
the user to replace it with one reviewed file. List multiple paths only when the user
has named those exact files to include. Make clear staging and committing are optional;
do not recommend `git add .` as a default troubleshooting step or suggest ignoring files
unless asked.

### `fatal: not a git repository`

Git cannot find repository metadata from the current directory or its parents. The
metadata is usually a `.git` directory, but worktrees can use a `.git` file. Check
`pwd` to identify the current location. If the intended repository path is already
known, change to that folder with `cd /path/to/project`, then run `git status`. If the
path is not known, ask for the output of `pwd` so the next `cd` command can be specific.
Do not recommend `git init` for this error; it creates a new repository and does not
find an existing one.

### `Your local changes would be overwritten`

Git is protecting uncommitted work from an operation that could replace it. Inspect
`git status`, `git diff`, and `git diff --staged`. Commit, back up, or deliberately stash
the work before retrying; do not discard changes without the user's intent.

### Merge conflict

Run `git status` to see the conflicted files, inspect each file's conflict markers, and
edit the file to keep the intended result. Then stage only resolved files and complete
the merge or rebase using the instructions Git printed. Do not use a hard reset as a
general conflict fix.

### Push rejected / non-fast-forward

The remote branch has commits not present in the local branch, or branch histories
differ. Inspect `git status`, `git branch --show-current`, and `git log --oneline --graph
--decorate -8`. Fetching can inspect remote updates without merging; do not recommend
force-pushing until the branch ownership and impact on collaborators are clear.
