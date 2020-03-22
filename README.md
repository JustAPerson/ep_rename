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

By default, `ep_rename.py` will extract the first thing that looks like an
episode number. This doesn't work well if a show title includes a number.
Consider the following file name:

    [a-s]_code_geass_r2_-_01_[1080p_bd-rip].mkv
    [a-s]_code_geass_r2_-_02_[1080p_bd-rip].mkv
    ...

By default, `ep_rename.py` will infer that both of those are episode two.
However, the way it parses file names can be changed with the `--input-fmt`
flag. Using the flag `--input-fmt "[a-s]_code_geass_r2_-_%n%a.%f"` will
correctly parse the file name. Additionally, you can specify even less detail and
still parse the file name using more advanced patterns such as
`"%b%a_r2_%n%a.%f"`. See the Input Format section below.


# Flags

<table>
  <tr>
    <th>Flag</th>
    <th>Details</th>
  </tr>
  <tr>
    <td><code>-d DIR</code> <br> <code>--destination DIR</code></td>
    <td>The destination directory where new files links will be created.
          Assumed to be the current directory.</td>
  </tr>
  <tr>
    <td><code>--output-type {symlink,hardlink,copy,move}</code></td>
    <td>Specifies the file type used for the output. Both <code>symlink</code> and
          <code>hardlink</code> take negligibly additional disk space whereas <code>copy</code>
          makes an extra copy of the file. Finally, <code>move</code> simply moves
          the existing file from one location to another.</td>
  </tr>
  <tr>
    <td><code>--first N</code></td>
    <td>Only act on the first N files in sorted order.</td>
  </tr>
  <tr>
    <td><code>--skip N</code></td>
    <td>Skip the first N files in sorted order. Implies <code>--renumber</code>.</td>
  </tr>
  <tr>
    <td><code>-t TITLE</code> <br> <code>--title TITLE</code></td>
    <td>The title to begin each file name with.</td>
  </tr>
  <tr>
    <td><code>-s SEASON</code><br><code>--season SEASON</code></td>
    <td>If specified, episode numbers will follow the s1e1 s1e2 etc pattern.
          The inverse can be done with <code>--strip-season</code></td>
  </tr>
  <tr>
    <td><code>--renumber</code><br><code>--no-renumber</code></td>
    <td>Number files beginning at 1 in order rather than using extracted
          episode number. This is useful if you have multiple seasons and the
          episode numbers do not reset to 1 at the beginning of each season.
          Implies <code>--renumber-start 1</code></td>
  </tr>
  <tr>
    <td><code>--renumber-start N</code></td>
    <td>Start renumbering files beginning at N instead of 1.</td>
  </tr>
  <tr>
    <td><code>--strip-season</code></td>
    <td>If the input files follow the s1e1 s1e2 etc pattern, remove the
          season prefix and renumber the files such that the first episode of
          season two is numbered directly after last episode of season one.
          Implies <code>--renumber --renumer-start 1</code></td>
  </tr>
  <tr>
    <td><code>--strip-leading-zeros</code></td>
    <td>Change the season or episode number from 01 to 1 etc.</td>
  </tr>
  <tr>
    <td><code>--zero-pad [WIDTH]</code></td>
    <td>Left pad episode numbers so they all are at least WIDTH length.
          If WIDTH is absent, it calculated based on the longest episode
          number. (Example: with WIDTH=3, then episode 1 becomes 001).</td>
  </tr>
  <tr>
    <td><code>--overwrite</code></td>
    <td>Overwrite the destination file if it exists. If this flag is not
          passed but any destination file already exists, an error will
          occur before creating any output files.</td>
  </tr>
  <tr>
    <td><code>--resolve-overlaps {error,newest,oldest,any}</code></td>
    <td>The method for resolving conflicts when multiple source files
          generate the same output file. The <code>newest</code> and <code>oldest</code> choices
          will use the source files' modified timestamp (resolving symbolic 
          links). Use the <code>any</code> choice if you don't care which file is chosen.</td>
  </tr>
  <tr>
    <td><code>--input-fmt FMT</code></td>
    <td>Specifies how the input file name should be parsed. See the INPUT
          FORMAT section below for details. The default is <code>%b%a%n%a.%f</code></td>
  </tr>
  <tr>
    <td><code>--dry</code></td>
    <td>Perform a dry run; don't modify the filesystem.</td>
  </tr>
  <tr>
    <td><code>-v</code><br><code>--verbose</code></td>
    <td>Specify what files are created. Use <code>-vv</code> to see more details.</td>
  </tr>
</table>

## Input Format

When traversing the current directory, file names are matched against the
format string specified by `--input-fmt`. If a name matches, the file is
kept and the desired fields are extracted. Files whose name do not match
are ignored.

A format string consists of sequence of literal characters and pattern
groups which begin with a `%`. Some pattern groups capture their matched
data which is used to determine metadata fields from the file name, such
as the season and episode number. The following pattern groups apply:

<table>
  <tr>
    <th>Group Pattern</th>
    <th>Details</th>
  </tr>
  <tr>
    <td><code>%a</code></td>
    <td>Matches any sequences of characters.</td>
  </tr>
  <tr>
    <td><code>%A</code></td>
    <td>Matches any positive-length sequence of characters.</td>
  </tr>
  <tr>
    <td><code>%b</code></td>
    <td>Optionally matches multiple pairs of square bracket and the content
        between them. Cannot handle nested brackets.</td>
  </tr>
  <tr>
    <td><code>%n</code></td>
    <td>Matches and captures a general episode number, which may or may not
        specify a season number. If it specifies a season number, it must
        follow the s1e1 pattern, case insensitive. In that case, both season
        and specific episode numbers are extracted. This pattern group may
        also match a single sequence of digits which will be interpreted as
        the specific episode number.</td>
  </tr>
  <tr>
    <td><code>%f</code></td>
    <td>Matches and captures the remaining non-dot characters of the file name and
        interprets it as the file name suffix to include on the output file.</td>
  </tr>
  <tr>
    <td><code>%%</code></td>
    <td>Matches the literal character <code>%</code>.</td>
  </tr>
</table>
