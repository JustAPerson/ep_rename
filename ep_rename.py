#!/usr/bin/env python3
"""
Copyright 2020 Jason Priest

Permission is hereby granted, free of charge,  to any person obtaining a copy of
this software  and associated documentation  files (the "Software"), to  deal in
the Software  without restriction,  including without  limitation the  rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to  whom the Software is furnished to do so,
subject to the following conditions:

The above copyright  notice and this permission notice shall  be included in all
copies or substantial portions of the Software.

THE  SOFTWARE IS  PROVIDED "AS  IS", WITHOUT  WARRANTY OF  ANY KIND,  EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR  PURPOSE AND NONINFRINGEMENT. IN NO EVENT  SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE  LIABLE FOR ANY CLAIM, DAMAGES OR  OTHER LIABILITY, WHETHER
IN  AN ACTION  OF  CONTRACT, TORT  OR  OTHERWISE,  ARISING FROM,  OUT  OF OR  IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import argparse
from pathlib import Path
import re
import sys

argparser = argparse.ArgumentParser(
    description='Canonicalizes episode filenames using symbolic links',
    usage='ep_rename.py [OPTIONS] -t TITLE',
    epilog='''
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
''',
    add_help=False,
    formatter_class=argparse.RawDescriptionHelpFormatter
)
argparser.add_argument(
    '-h', '--help',
    action='help',
    help='Display this help message.'
)
argparser.add_argument(
    '-d', '--destination',
    metavar='DIR',
    help='The destination directory where new symbolic links will be created. \
          Assumed to be the current directory.'
)
argparser.add_argument(
    '--first',
    metavar='N',
    help='Only act on the first N files in sorted order.'
)
argparser.add_argument(
    '--skip',
    metavar='N',
    help='Skip the first N files in sorted order. Implies `--renumber`.'
)
argparser.add_argument(
    '-t', '--title',
    required=True,
    help='The title to begin each filename with.'
)
argparser.add_argument(
    '-s', '--season',
    help='If specified, episode numbers will follow the s1e1 s1e2 etc pattern. \
          The inverse can be done with `--strip-season`'
)
class NegateAction(argparse.Action):
    """Taken from https://stackoverflow.com/a/34736291/5991105"""
    def __call__(self, parser, ns, values, option):
        setattr(ns, self.dest, option[2:4] != 'no')
argparser.add_argument(
    '--renumber', '--no-renumber',
    action=NegateAction,
    nargs=0,
    dest='renumber',
    help='Number files beginning at 1 in order rather than using extracted \
          episode number. This is useful if you have multiple seasons and the \
          episode numbers do not reset to 1 at the beginning of each season.'
)
argparser.add_argument(
    '--strip-leading-zeros',
    action='store_true',
    help='Change the episode number from 01 to 1 etc.'
)
class AUTO_ZERO_PAD:
    def __int__(self):
        return 1
argparser.add_argument(
    '--zero-pad',
    nargs='?',
    metavar='WIDTH',
    const=AUTO_ZERO_PAD(),
    help='Left pad episode numbers so they all are at least WIDTH length. \
          If WIDTH is absent, it calculated based on the longest episode \
          number. (Example: with WIDTH=3, then episode 1 becomes 001).'
)
argparser.add_argument(
    '--overwrite',
    action='store_true',
    help='Overwrite the destination file if it exists. If this flag is not \
          passed but any destination file already exists, an error will \
          occur before creating any symbolic links.'
)
argparser.add_argument(
    '--resolve-overlaps',
    choices=['error', 'newest', 'oldest', 'any'],
    default = 'error',
    help='The method for resolving conflicts when multiple source files \
          generate the same output file. The `newest` and `oldest` choices \
          will use the source files\' modified timestamp (resolving symbolic  \
          links). Use the `any` choice if you don\'t care which file is chosen.'
)
argparser.add_argument(
    '--dry',
    action='store_true',
    help='Perform a dry run; don\'t modify the filesystem.'
)
argparser.add_argument(
    '-v', '--verbose',
    action='count',
    default=0,
    help='Specify what files are created. Use `-vv` to see more details.'
)


def sort_inputs_by_time(paths):
    paths.sort(key=lambda p: p['file'].stat().st_mtime)

def sort_inputs_by_num(parts):
    parts.sort(key=lambda p: int(p['number'])) # handle sorting ep 101 after episode 2

class Program:
    def __init__(self, args):
        self.args = args

    def log(self, level, msg):
        if level <= self.args.verbose:
            print(msg, file=sys.stderr)

    def extract_parts(self, f):
        # remove group prefixes like `./[SubGroup] Title.mkv`
        without_group = re.fullmatch(r'(?:\[.*?\])?(.*)', f.name).group(1)
        number, suffix = re.search(r'([0-9]+).*(\..+)', without_group).group(1, 2)

        self.log(2,
                 'extracted number={!r} suffix={!r} from file={!r}'
                 .format(number, suffix, str(f)))

        return { 'file': f, 'number': number, 'suffix': suffix }

    def run(self):
        files = [f for f in Path('.').iterdir() if f.is_file()]
        parts = list(map(self.extract_parts, files))
        sort_inputs_by_num(parts)

        if self.args.skip:
            skip = int(self.args.skip)
            if skip >= len(parts):
                self.log(0, 'warning: skipping all files')
            parts = parts[skip:]

        if self.args.first:
            first = int(self.args.first)
            if first > len(parts):
                self.log(0, 'warning: there are only {} files but given --first={}'
                            .format(len(parts), first))
            parts = parts[:first]

        self.try_renumber_or_strip_leading_zeros(parts)
        self.try_zero_pad(parts)
        self.calc_destinations(parts)

        self.check_overlaps(parts)
        self.check_overwrites(parts)

        for p in parts:
            old = p['file']
            new = p['dest']
            if not self.args.dry:
                if self.args.overwrite and new.exists():
                    self.log(0, 'removing existing file ' + repr(str(new)))
                    new.unlink()
                new.symlink_to(old.resolve())
            self.log(1, 'created symbolic link from {!r} to {!r}'.format(str(new), str(old)))

    def try_renumber_or_strip_leading_zeros(self, parts):
        if self.args.renumber:
            i = 1
            for p in parts:
                self.log(2, 'renumbered {} to {}'.format(p['number'], i))
                p['number'] = str(i)
                i += 1
        elif self.args.strip_leading_zeros:
            for p in parts:
                numer = p['number']
                if number.startswith('0') and len(number) > 1:
                    self.log(2, 'renumbered {} to {}'.format(number, i))
                    p['number'] = number.lstrip('0')

    def try_zero_pad(self, parts):
        if self.args.zero_pad:
            if type(self.args.zero_pad) is AUTO_ZERO_PAD:
                width = max(map(lambda p: len(p['number']), parts))
            else:
                width = int(self.args.zero_pad)

            fmt = '{{:0>{}}}'.format(width)
            for p in parts:
                old = p['number']
                new = fmt.format(old)
                p['number'] = new
                self.log(2, 'renumbered {} to {}'.format(old, new))


    def calc_destinations(self, parts):
        ep_prefix = 's{}e'.format(self.args.season) if self.args.season else ''
        for p in parts:
            name = '{} {}{number}{suffix}'.format(self.args.title, ep_prefix, **p)
            p['dest'] = Path(self.args.destination or './', name)


    def check_overwrites(self, parts):
        if not self.args.overwrite:
            oops = [d for d in map(lambda p: p['dest'], parts) if d.exists()]
            if len(oops) > 0:
                self.log(0, 'the following files already exist:')
                for oop in oops:
                    self.log(0, '  ' + str(oop))
                self.log(0, '')
                self.log(0, 'use the `--overwrite` flag to ignore these.')
                sys.exit(1)

    def check_overlaps(self, parts):
        if len(parts) == len(set(map(lambda p: p['dest'], parts))):
            # each input maps to a unique output
            return

        sources_dict = {}
        for p in parts:
            dest = str(p['dest'])
            src = p
            sources_dict[dest] = sources_dict.get(dest, []) + [src]
        oops = filter((lambda item: len(item[1]) > 1), sources_dict.items())
        oops = sorted(oops)

        if self.args.resolve_overlaps == 'error':
            for dest, sources in oops:
                sort_inputs_by_time(sources)
                self.log(0, 'the following files all map to {!r}:'.format(dest))
                for src in sources:
                    self.log(0, '  ' + str(src['file']))
            self.log(0, '')
            self.log(0, 'use the `--resolve-overlaps` flag to proceed')
            self.log(0, 'files above are already shown in ascending date order')
            sys.exit(1)
        else:
            def oldest(paths):
                sort_inputs_by_time(paths)
                return paths[0], paths[1:]

            def newest(paths):
                sort_inputs_by_time(paths)
                return paths[-1], paths[:-1]

            def any(paths):
                return paths[0], paths[1:]

            methods = {
                'oldest': oldest,
                'newest': newest,
                'any': any,
            }
            method = methods[self.args.resolve_overlaps]

            remove = []
            self.log(1, 'using overlap resolution: ' + self.args.resolve_overlaps)
            for _, sources in oops:
                chosen, ignored = method(sources)
                self.log(1, 'choosing {!r} for {!r} in favor of {!r}'
                            .format(str(chosen['file']), dest, [str(i['file']) for i in ignored]))
                remove += ignored

            for p in remove:
                # O(n^2) but who will have 1000 files all overlapping? ....
                # Much easier than trying to perform set operations dicts
                parts.remove(p)

def is_nonneg(s):
    try:
        return int(s) >= 0
    except ValueError:
        return False

args = argparser.parse_args()

if args.renumber and args.strip_leading_zeros:
    argparser.error('cannot specify both `--renumber` and `--strip-leading-zeros`')

if args.strip_leading_zeros and arg.zero_pad:
    argparser.error('cannot specify both `--zero_pad` and `--strip-leading-zeros`')

if args.destination and not Path(args.destination).is_dir():
    argparser.error('`--destination` must refer to a valid directory')

if args.zero_pad and not is_nonneg(args.zero_pad):
    argparser.error('must specify a positive integer to `--zero-pad`')

if args.first and not is_nonneg(args.first):
    argparser.error('must specify a positive integer to `--first`')

if args.skip and not is_nonneg(args.skip):
    argparser.error('must specify a positive integer to `--skip`')

if (args.skip or args.first) and not args.destination:
    argparser.error('must specify a destination with `--destination` while '
                    + 'using `--skip` or `--first` because they will change '
                    + 'the set of files in this directory')

if args.skip and args.renumber is None:
    args.renumber = True

Program(args).run()
