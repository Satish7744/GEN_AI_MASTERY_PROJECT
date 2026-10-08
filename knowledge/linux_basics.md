# Linux command line basics

## Where am I and what is here?

`pwd` prints the current working directory. `ls` lists directory contents. `ls -la`
also shows hidden files and details. `cd path` changes directories; `cd ..` moves to
the parent directory and `cd ~` moves to the home directory.

## Read files and search text

`cat file.txt` prints a short file. `less file.txt` opens a file for scrolling. `head`
and `tail` show the beginning and end of a file; `tail -f logfile` follows new lines.
`grep -n "pattern" file.txt` searches text and includes line numbers. `find . -name
"*.txt"` searches below the current directory for matching names.

## Files and directories

`mkdir notes` creates a directory. `cp source destination` copies. `mv source
destination` moves or renames. `rm file` permanently removes a file, and `rm -r
directory` can permanently remove a directory tree. Check the path with `pwd` and
`ls` before using `rm`; use an interactive option such as `rm -i file` when unsure.

## Permissions

`chmod` changes file permissions. Numeric modes such as `chmod 644 file` set owner
read/write and group/other read permissions. Avoid broad modes such as `chmod -R 777`
because they grant everyone read, write, and execute access recursively.

## Processes and help

`ps` lists processes; `top` shows a live process view. `command --help` and `man
command` show usage information. `sudo` runs a command with elevated privileges; only
use it when you understand why administrative access is needed.
