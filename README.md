# `ep_rename.py`

This tool can help organize episodic files into a standardized naming convention.

# Usage 

Consider a directory with the following files:

    ./fullmetal_alchemist_brotherhood_-_01_[1080p_bd-rip].mkv
    ./fullmetal_alchemist_brotherhood_-_02_[1080p_bd-rip].mkv
    ./fullmetal_alchemist_brotherhood_-_03_[1080p_bd-rip].mkv
    ...

Running `ep_rename.py -t "Fullmetal Alchemist Brotherhood"` will create the
following symbolic links in the same directory:

    ./Fullmetal Alchemist Brotherhood 01.mkv
    ./Fullmetal Alchemist Brotherhood 02.mkv
    ./Fullmetal Alchemist Brotherhood 03.mkv
    ...

You could add `--strip-leading-zeros` to do the obvious, or use `--zero-pad 3`
to add an extra zero. If you had 100 episodes, `--zero-pad` without an argument
will automatically deduce the width should be three.

Consider a directory with multiple seasons worth all numbered sequentially:

    ./Dragon Ball - 001 [x264].mkv
    ./Dragon Ball - 002 [x264].mkv
    ...
    ./Dragon Ball - 153 [x264].mkv

You can use the `--season 1 --first 13` flags once followed by using the
`--season 2 --first 13 --skip 13` flags and so forth until you end up with each
season split as follows:

    ./Dragon Ball s1e1.mkv
    ./Dragon Ball s1e2.mkv
    ...
    ./Dragon Ball s1e13.mkv
    ./Dragon Ball s2e1.mkv
    ./Dragon Ball s2e2.mkv
    ...

You will want to use `--destination` along with that so that the second
time you run `ep_rename.py` it doesn't try to use the files you just made.
