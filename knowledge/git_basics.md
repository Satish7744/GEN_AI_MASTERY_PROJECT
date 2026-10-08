# Git basics

## Inspect the repository

`git status` shows the current branch and working-tree changes. `git log --oneline
--decorate -5` shows recent commits. `git diff` shows unstaged changes and `git diff
--staged` shows staged changes. Inspect these before committing or undoing work.

## Stage and commit

`git add file.txt` stages one file. `git add .` stages all changes under the current
directory, so inspect `git status` first. `git commit -m "Describe the change"`
creates a commit from staged changes. A commit is local until pushed.

## Branches and remotes

`git branch --show-current` prints the current branch. `git switch -c feature-name`
creates and switches to a branch. `git remote -v` lists remote URLs. `git fetch`
downloads remote updates without merging them into the current branch.

## Undo carefully

`git restore -- file.txt` discards unstaged changes in that file. This can lose work;
inspect with `git diff` first. `git restore --staged -- file.txt` unstages a file but
keeps its working-tree contents. `git revert COMMIT` creates a new commit that
reverses an earlier commit and is usually safer for shared history. `git reset --hard`
discards tracked working-tree changes and moves the current branch; do not suggest it
without first checking status and explaining data loss.

## Sync with a remote

`git pull` fetches and integrates remote changes. Review your working tree and branch
before pulling. If Git reports conflicts, open the listed files, resolve conflict
markers, then stage the resolved files and complete the merge or rebase as instructed.
