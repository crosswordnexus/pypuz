"""
Library for reading and writing Across Lite (.puz) files.
Originally based on puzpy by Alex Dejarnatt.
"""

import functools
import operator
import math
import string
import struct
import sys

__title__ = 'puzpy'
__version__ = '0.2.3'
__author__ = 'Alex DeJarnatt'
__author_email__ = 'adejarnatt@gmail.com'
__maintainer__ = 'Simeon Visser'
__maintainer_email__ = 'simeonvisser@gmail.com'
__license__ = 'MIT'
__copyright__ = 'Copyright 2009 Alex DeJarnatt'


PY3 = sys.version_info[0] >= 3

if PY3:
    str = str
    range = range
else:
    str = unicode  # noqa: F821
    range = xrange  # noqa: F821

# Binary format for the .puz header
HEADER_FORMAT = '''<
             H 11s        xH
             Q       4s  2sH
             12s         BBH
             H H '''

HEADER_CKSUM_FORMAT = '<BBH H H '

EXTENSION_HEADER_FORMAT = '< 4s  H H '

MASKSTRING = 'ICHEATED'

ENCODING = 'ISO-8859-1'
ENCODING_UTF8 = 'UTF-8'
ENCODING_ERRORS = 'strict'  # raises an exception for bad chars; change to 'replace' for laxer handling

ACROSSDOWN = b'ACROSS&DOWN'

BLACKSQUARE = '.'
BLACKSQUARE2 = ':'


def enum(**enums):
    """Helper to create a simple enumeration-like type."""
    return type('Enum', (), enums)


PuzzleType = enum(
    Normal=0x0001,
    Diagramless=0x0401
)

# Solution state constants
SolutionState = enum(
    # solution is available in plaintext
    Unlocked=0x0000,
    # solution is locked (scrambled) with a key
    Locked=0x0004
)

# Grid markup flags
GridMarkup = enum(
    # ordinary grid cell
    Default=0x00,
    # marked incorrect at some point
    PreviouslyIncorrect=0x10,
    # currently showing incorrect
    Incorrect=0x20,
    # user got a hint
    Revealed=0x40,
    # circled
    Circled=0x80
)


# Extension codes used in .puz files
Extensions = enum(
    # grid of rebus indices: 0 for non-rebus;
    # i+1 for key i into RebusSolutions map
    Rebus=b'GRBS',
    # map of rebus solution entries eg 0:HEART;1:DIAMOND;17:CLUB;23:SPADE;
    RebusSolutions=b'RTBL',
    # user's rebus entries
    RebusFill=b'RUSR',
    # timer state: 'a,b' where a is the number of seconds elapsed and
    # b is a boolean (0,1) for whether the timer is running
    Timer=b'LTIM',
    # grid cell markup: previously incorrect: 0x10;
    # currently incorrect: 0x20,
    # hinted: 0x40,
    # circled: 0x80
    Markup=b'GEXT'
)


def read(filename):
    """
    Read a .puz file and return a Puzzle object.

    Args:
        filename (str): Path to the .puz file.

    Returns:
        Puzzle: The parsed puzzle object.

    Raises:
        PuzzleFormatError: If the file is not a valid .puz file.
    """
    with open(filename, 'rb') as f:
        return load(f.read())


def load(data):
    """
    Load .puz file data and return a Puzzle object.

    Args:
        data (bytes): Raw binary data of a .puz file.

    Returns:
        Puzzle: The parsed puzzle object.

    Raises:
        PuzzleFormatError: If the data is not a valid .puz file.
    """
    puz = Puzzle()
    puz.load(data)
    return puz


class PuzzleFormatError(Exception):
    """
    Indicates a format error in the .puz file. May be thrown due to
    invalid headers, invalid checksum validation, or other format issues.
    """
    def __init__(self, message=''):
        self.message = message


class Puzzle:
    """
    Represents an Across Lite (.puz) puzzle.
    
    Contains all puzzle data including metadata, grid, clues, and extensions.
    """
    def __init__(self):
        """Initializes a blank puzzle with default values."""
        self.preamble = b''
        self.postscript = b''
        self.title = ''
        self.author = ''
        self.copyright = ''
        self.width = 0
        self.height = 0
        self.version = b'1.3'
        self.fileversion = b'1.3\0'  # default
        self.encoding = ENCODING
        # these are bytes that might be unused
        self.unk1 = b'\0' * 2
        self.unk2 = b'\0' * 12
        self.scrambled_cksum = 0
        self.fill = ''
        self.solution = ''
        self.clues = []
        self.notes = ''
        self.extensions = {}
        # the following is so that we can round-trip values in order:
        self._extensions_order = []
        self.puzzletype = PuzzleType.Normal
        self.solution_state = SolutionState.Unlocked
        self.helpers = {}  # add-ons like Rebus and Markup

    def load(self, data):
        """
        Populate the puzzle object from raw binary data.

        Args:
            data (bytes): The binary data to parse.
        """
        s = PuzzleBuffer(data)

        # advance to start - files may contain some data before the
        # start of the puzzle use the ACROSS&DOWN magic string as a waypoint
        # save the preamble for round-tripping
        if not s.seek_to(ACROSSDOWN, -2):
            raise PuzzleFormatError("Data does not appear to represent a "
                                    "puzzle. Are you sure you didn't intend "
                                    "to use read?")

        self.preamble = s.data[:s.pos]

        puzzle_data = s.unpack(HEADER_FORMAT)
        cksum_gbl = puzzle_data[0]
        # acrossDown = puzzle_data[1]
        cksum_hdr = puzzle_data[2]
        cksum_magic = puzzle_data[3]
        self.fileversion = puzzle_data[4]
        # since we don't know the role of these bytes, just round-trip them
        self.unk1 = puzzle_data[5]
        self.scrambled_cksum = puzzle_data[6]
        self.unk2 = puzzle_data[7]
        self.width = puzzle_data[8]
        self.height = puzzle_data[9]
        numclues = puzzle_data[10]
        self.puzzletype = puzzle_data[11]
        self.solution_state = puzzle_data[12]

        self.version = self.fileversion[:3]
        # Once we have fileversion we can guess the encoding
        self.encoding = ENCODING if self.version_tuple()[0] < 2 else ENCODING_UTF8
        s.encoding = self.encoding

        self.solution = s.read(self.width * self.height).decode(self.encoding)
        self.fill = s.read(self.width * self.height).decode(self.encoding)

        self.title = s.read_string()
        self.author = s.read_string()
        self.copyright = s.read_string()

        self.clues = [s.read_string() for i in range(0, numclues)]
        self.notes = s.read_string()

        # Parse extensions (rebus, markup, etc.)
        ext_cksum = {}
        while s.can_unpack(EXTENSION_HEADER_FORMAT):
            code, length, cksum = s.unpack(EXTENSION_HEADER_FORMAT)
            ext_cksum[code] = cksum
            # extension data is represented as a null-terminated string,
            # but since the data can contain nulls we can't use read_string
            self.extensions[code] = s.read(length)
            s.read(1)  # extensions have a trailing byte
            # save the codes in order for round-tripping
            self._extensions_order.append(code)

        # sometimes there's some extra garbage at
        # the end of the file, usually \r\n
        if s.can_read():
            self.postscript = s.read_to_end()

        # Validation: Verify all checksums
        if cksum_gbl != self.global_cksum():
            raise PuzzleFormatError('global checksum does not match')
        if cksum_hdr != self.header_cksum():
            raise PuzzleFormatError('header checksum does not match')
        if cksum_magic != self.magic_cksum():
            raise PuzzleFormatError('magic checksum does not match')
        for code, cksum_ext in ext_cksum.items():
            if cksum_ext != data_cksum(self.extensions[code]):
                raise PuzzleFormatError(
                    'extension %s checksum does not match' % code
                )

    def save(self, filename):
        """
        Write the puzzle to a file in .puz format.

        Args:
            filename (str): The path to the file to create.
        """
        puzzle_bytes = self.tobytes()
        with open(filename, 'wb') as f:
            f.write(puzzle_bytes)

    def tobytes(self):
        """
        Return the puzzle as a binary string in .puz format.

        Returns:
            bytes: Binary representation of the puzzle.
        """
        s = PuzzleBuffer(encoding=self.encoding)
        # commit any changes from helpers (Rebus/Markup)
        for h in self.helpers.values():
            if 'save' in dir(h):
                h.save()

        # include any preamble text we might have found on read
        s.write(self.preamble)

        s.pack(HEADER_FORMAT,
               self.global_cksum(), ACROSSDOWN,
               self.header_cksum(), self.magic_cksum(),
               self.fileversion, self.unk1, self.scrambled_cksum,
               self.unk2, self.width, self.height,
               len(self.clues), self.puzzletype, self.solution_state)

        s.write(self.encode(self.solution))
        s.write(self.encode(self.fill))

        s.write_string(self.title)
        s.write_string(self.author)
        s.write_string(self.copyright)

        for clue in self.clues:
            s.write_string(clue)

        s.write_string(self.notes)

        # Ensure extensions round-trip in the order they were read.
        ext = dict(self.extensions)
        for code in self._extensions_order:
            data = ext.pop(code, None)
            if data:
                s.pack(EXTENSION_HEADER_FORMAT, code,
                       len(data), data_cksum(data))
                s.write(data + b'\0')

        # Write any new extensions
        for code, data in ext.items():
            s.pack(EXTENSION_HEADER_FORMAT, code, len(data), data_cksum(data))
            s.write(data + b'\0')

        # Convert postscript to bytes if it was modified as a string
        try:
            postscript_bytes = self.encode(self.postscript)
        except AttributeError:
            postscript_bytes = self.postscript

        s.write(postscript_bytes)

        return s.tobytes()

    def encode(self, s):
        """Encode a string according to the puzzle's encoding."""
        return s.encode(self.encoding, ENCODING_ERRORS)

    def encode_zstring(self, s):
        """Encode a string and append a null terminator."""
        return self.encode(s) + b'\0'

    def version_tuple(self):
        """Return the version as a tuple of integers."""
        return tuple(map(int, self.version.split(b'.')))

    def has_rebus(self):
        """Check if the puzzle contains rebus data."""
        return self.rebus().has_rebus()

    def rebus(self):
        """Return the Rebus helper object."""
        return self.helpers.setdefault('rebus', Rebus(self))

    def has_markup(self):
        """Check if the puzzle contains markup data (e.g., circles)."""
        return self.markup().has_markup()

    def markup(self):
        """Return the Markup helper object."""
        return self.helpers.setdefault('markup', Markup(self))

    def clue_numbering(self):
        """Return the ClueNumbering helper object."""
        numbering = DefaultClueNumbering(self.fill, self.clues, self.width, self.height)
        return self.helpers.setdefault('clues', numbering)

    def blacksquare(self):
        """Return the character used for black squares in this puzzle."""
        return BLACKSQUARE2 if self.puzzletype == PuzzleType.Diagramless else BLACKSQUARE

    def is_solution_locked(self):
        """Check if the solution is scrambled."""
        return bool(self.solution_state != SolutionState.Unlocked)

    def unlock_solution(self, key):
        """
        Attempt to unscramble the solution using the provided key.

        Args:
            key (int): 4-digit numeric key.

        Returns:
            bool: True if unlocking was successful, False otherwise.
        """
        if self.is_solution_locked():
            unscrambled = unscramble_solution(self.solution, self.width, self.height, key,
                                              ignore_chars=self.blacksquare())
            if not self.check_answers(unscrambled):
                return False

            # clear the scrambled bit and cksum
            self.solution = unscrambled
            self.scrambled_cksum = 0
            self.solution_state = SolutionState.Unlocked

        return True

    def lock_solution(self, key):
        """
        Scramble the solution using the provided key.

        Args:
            key (int): 4-digit numeric key.
        """
        if not self.is_solution_locked():
            # set the scrambled bit and cksum
            self.scrambled_cksum = scrambled_cksum(self.solution, self.width, self.height,
                                                   ignore_chars=self.blacksquare(), encoding=self.encoding)
            self.solution_state = SolutionState.Locked
            scrambled = scramble_solution(self.solution, self.width, self.height, key,
                                          ignore_chars=self.blacksquare())
            self.solution = scrambled

    def check_answers(self, fill):
        """Verify if the provided fill matches the solution (or its checksum)."""
        if self.is_solution_locked():
            scrambled = scrambled_cksum(fill, self.width, self.height,
                                        ignore_chars=self.blacksquare(), encoding=self.encoding)
            return scrambled == self.scrambled_cksum
        else:
            return fill == self.solution

    def header_cksum(self, cksum=0):
        """Calculate the checksum for the header fields."""
        return data_cksum(struct.pack(HEADER_CKSUM_FORMAT,
                          self.width, self.height, len(self.clues),
                          self.puzzletype, self.solution_state), cksum)

    def text_cksum(self, cksum=0):
        """Calculate the checksum for the text fields (title, author, clues, etc.)."""
        # for the checksum to work these fields must be added in order with
        # null termination, followed by all non-empty clues without null
        # termination, followed by notes (but only for version >= 1.3)
        if self.title:
            cksum = data_cksum(self.encode_zstring(self.title), cksum)
        if self.author:
            cksum = data_cksum(self.encode_zstring(self.author), cksum)
        if self.copyright:
            cksum = data_cksum(self.encode_zstring(self.copyright), cksum)

        for clue in self.clues:
            if clue:
                cksum = data_cksum(self.encode(clue), cksum)

        # notes included in global cksum starting v1.3 of format
        if self.version_tuple() >= (1, 3) and self.notes:
            cksum = data_cksum(self.encode_zstring(self.notes), cksum)

        return cksum

    def global_cksum(self):
        """Calculate the overall file checksum."""
        cksum = self.header_cksum()
        cksum = data_cksum(self.encode(self.solution), cksum)
        cksum = data_cksum(self.encode(self.fill), cksum)
        cksum = self.text_cksum(cksum)
        # extensions do not seem to be included in global cksum
        return cksum

    def magic_cksum(self):
        """Calculate the 'magic' checksum used in Across Lite files."""
        cksums = [
            self.header_cksum(),
            data_cksum(self.encode(self.solution)),
            data_cksum(self.encode(self.fill)),
            self.text_cksum()
        ]

        cksum_magic = 0
        for (i, cksum) in enumerate(reversed(cksums)):
            cksum_magic <<= 8
            cksum_magic |= (
                ord(MASKSTRING[len(cksums) - i - 1]) ^ (cksum & 0x00ff)
            )
            cksum_magic |= (
                (ord(MASKSTRING[len(cksums) - i - 1 + 4]) ^ (cksum >> 8)) << 32
            )

        return cksum_magic


class PuzzleBuffer:
    """
    Wraps a data buffer and provides .puz-specific methods for
    reading and writing data types.
    """
    def __init__(self, data=None, encoding=ENCODING):
        self.data = data or []
        self.encoding = encoding
        self.pos = 0

    def can_read(self, n_bytes=1):
        """Check if n_bytes can be read from the current position."""
        return self.pos + n_bytes <= len(self.data)

    def length(self):
        """Return the total length of the buffer data."""
        return len(self.data)

    def read(self, n_bytes):
        """Read n_bytes from the buffer."""
        start = self.pos
        self.pos += n_bytes
        return self.data[start:self.pos]

    def read_to_end(self):
        """Read all remaining data from the current position."""
        start = self.pos
        self.pos = self.length()
        return self.data[start:self.pos]

    def read_string(self):
        """Read a null-terminated string."""
        return self.read_until(b'\0')

    def read_until(self, c):
        """Read until the sequence c is encountered."""
        start = self.pos
        self.seek_to(c, 1)  # read past the character
        return str(self.data[start:self.pos-1], self.encoding)

    def seek_to(self, s, offset=0):
        """Move the position to the first occurrence of s, plus offset."""
        try:
            self.pos = self.data.index(s, self.pos) + offset
            return True
        except ValueError:
            # s not found, advance to end
            self.pos = self.length()
            return False

    def write(self, s):
        """Append data to the buffer."""
        self.data.append(s)

    def write_string(self, s):
        """Encode and append a null-terminated string to the buffer."""
        s = s or ''
        self.data.append(s.encode(self.encoding, ENCODING_ERRORS) + b'\0')

    def pack(self, struct_format, *values):
        """Pack values using struct.pack and append to the buffer."""
        self.data.append(struct.pack(struct_format, *values))

    def can_unpack(self, struct_format):
        """Check if there is enough data to unpack the given format."""
        return self.can_read(struct.calcsize(struct_format))

    def unpack(self, struct_format):
        """Unpack values from the current position using struct.unpack."""
        start = self.pos
        try:
            res = struct.unpack_from(struct_format, self.data, self.pos)
            self.pos += struct.calcsize(struct_format)
            return res
        except struct.error:
            message = 'could not unpack values at {} for format {}'.format(
                start, struct_format
            )
            raise PuzzleFormatError(message)

    def tobytes(self):
        """Return the buffer content as a single bytes object."""
        return b''.join(self.data)


class DefaultClueNumbering:
    """
    Helper class to calculate standard crossword clue numbering
    based on the grid's block positions.
    """
    def __init__(self, grid, clues, width, height):
        self.grid = grid
        self.clues = clues
        self.width = width
        self.height = height

        # compute across & down
        a = []
        d = []
        c = 0
        n = 1
        for i in range(0, len(grid)):
            if not is_blacksquare(grid[i]):
                lastc = c
                # A cell gets an Across number if it's at the start of a row
                # or preceded by a black square, and has at least one cell to its right.
                is_across = self.col(i) == 0 or is_blacksquare(grid[i - 1])
                if is_across and self.len_across(i) > 1:
                    a.append({
                        'num': n,
                        'clue': clues[c],
                        'clue_index': c,
                        'cell': i,
                        'len': self.len_across(i)
                    })
                    c += 1
                # A cell gets a Down number if it's at the top of a column
                # or preceded by a black square above it, and has at least one cell below.
                is_down = self.row(i) == 0 or is_blacksquare(grid[i - width])
                if is_down and self.len_down(i) > 1:
                    d.append({
                        'num': n,
                        'clue': clues[c],
                        'clue_index': c,
                        'cell': i,
                        'len': self.len_down(i)
                    })
                    c += 1
                # Increment clue number if this cell was the start of any clue
                if c > lastc:
                    n += 1

        self.across = a
        self.down = d

    def col(self, index):
        """Return the column index (0-based) for a linear grid index."""
        return index % self.width

    def row(self, index):
        """Return the row index (0-based) for a linear grid index."""
        return int(math.floor(index / self.width))

    def len_across(self, index):
        """Return the length of the across word starting at index."""
        for c in range(0, self.width - self.col(index)):
            if is_blacksquare(self.grid[index + c]):
                return c
        return c + 1

    def len_down(self, index):
        """Return the length of the down word starting at index."""
        for c in range(0, self.height - self.row(index)):
            if is_blacksquare(self.grid[index + c*self.width]):
                return c
        return c + 1


class Rebus:
    """
    Helper class for managing rebus (multi-character) cells in a .puz file.
    """
    def __init__(self, puzzle):
        self.puzzle = puzzle
        # parse rebus data from extensions
        rebus_data = self.puzzle.extensions.get(Extensions.Rebus, b'')
        self.table = parse_bytes(rebus_data)
        r_sol_data = self.puzzle.extensions.get(Extensions.RebusSolutions, b'')
        solutions_str = r_sol_data.decode(puzzle.encoding)
        fill_data = self.puzzle.extensions.get(Extensions.RebusFill, b'')
        fill_str = fill_data.decode(puzzle.encoding)
        self.solutions = dict(
            (int(item[0]), item[1])
            for item in parse_dict(solutions_str).items()
        )
        self.fill = dict(
            (int(item[0]), item[1])
            for item in parse_dict(fill_str).items()
        )

    def has_rebus(self):
        """Check if the puzzle has any rebus data."""
        return Extensions.Rebus in self.puzzle.extensions

    def is_rebus_square(self, index):
        """Check if the cell at index is a rebus square."""
        return bool(self.table and index < len(self.table) and self.table[index])

    def get_rebus_squares(self):
        """Return a list of indices of all rebus squares."""
        return [i for i, b in enumerate(self.table) if b]

    def get_rebus_solution(self, index):
        """Return the solution string for the rebus square at index."""
        if self.is_rebus_square(index):
            return self.solutions[self.table[index] - 1]
        return None

    def get_rebus_fill(self, index):
        """Return the user's fill for the rebus square at index."""
        if self.is_rebus_square(index):
            return self.fill[self.table[index] - 1]
        return None

    def set_rebus_fill(self, index, value):
        """Set the user's fill for the rebus square at index."""
        if self.is_rebus_square(index):
            self.fill[self.table[index] - 1] = value

    def save(self):
        """Commit rebus changes back to the puzzle's extensions."""
        if self.has_rebus():
            self.puzzle.extensions[Extensions.Rebus] = pack_bytes(self.table)
            rebus_solutions = self.puzzle.encode(dict_to_string(self.solutions))
            self.puzzle.extensions[Extensions.RebusSolutions] = rebus_solutions
            rebus_fill = self.puzzle.encode(dict_to_string(self.fill))
            self.puzzle.extensions[Extensions.RebusFill] = rebus_fill


class Markup:
    """
    Helper class for managing cell markup (circles, etc.) in a .puz file.
    """
    def __init__(self, puzzle):
        self.puzzle = puzzle
        # parse markup data from GEXT extension
        markup_data = self.puzzle.extensions.get(Extensions.Markup, b'')
        self.markup = parse_bytes(markup_data)

    def has_markup(self):
        """Check if any cell has markup applied."""
        return any(bool(b) for b in self.markup)

    def get_markup_squares(self):
        """Return a list of indices of all cells with markup."""
        return [i for i, b in enumerate(self.markup) if b]

    def is_markup_square(self, index):
        """Check if the cell at index has markup."""
        return bool(self.markup and index < len(self.markup) and self.markup[index])

    def save(self):
        """Commit markup changes back to the puzzle's extensions."""
        if self.has_markup():
            self.puzzle.extensions[Extensions.Markup] = pack_bytes(self.markup)


# helper functions for cksums and scrambling
def data_cksum(data, cksum=0):
    """
    Calculate a 16-bit checksum for the given data.
    
    This follows the Across Lite checksum algorithm: 
    Right-shift with wrap-around, then add the data byte.
    """
    for b in data:
        if isinstance(b, bytes):
            b = ord(b)
        # 16-bit right-shift one with wrap-around
        lowbit = (cksum & 0x0001)
        cksum = (cksum >> 1)
        if lowbit:
            cksum = (cksum | 0x8000)

        # then add in the data and clear any carried bit past 16
        cksum = (cksum + b) & 0xffff

    return cksum


def replace_chars(s, chars, replacement=''):
    """Replace all occurrences of characters in 'chars' with 'replacement'."""
    for ch in chars:
        s = s.replace(ch, replacement)
    return s


def scramble_solution(solution, width, height, key, ignore_chars=BLACKSQUARE):
    """
    Scramble the solution using the provided key.
    
    This is used to lock the solution in Across Lite files.
    """
    sq = square(solution, width, height)
    data = restore(sq, scramble_string(replace_chars(sq, ignore_chars), key))
    return square(data, height, width)


def scramble_string(s, key):
    """
    Internal string scrambling logic for Across Lite.
    
    Args:
        s: Solution in column-major order, omitting black squares.
        key: 4-digit number 1000-9999.
    """
    key = key_digits(key)
    for k in key:          # foreach digit in the key
        s = shift(s, key)  # for each char by each digit in the key in sequence
        s = s[k:] + s[:k]  # cut the sequence around the key digit
        s = shuffle(s)     # do a 1:1 shuffle of the 'deck'

    return s


def unscramble_solution(scrambled, width, height, key, ignore_chars=BLACKSQUARE):
    """Unscramble a scrambled solution using the provided key."""
    # width and height are reversed here to handle column-major logic
    sq = square(scrambled, width, height)
    data = restore(sq, unscramble_string(replace_chars(sq, ignore_chars), key))
    return square(data, height, width)


def unscramble_string(s, key):
    """Internal string unscrambling logic."""
    key = key_digits(key)
    l = len(s)  # noqa: E741
    for k in key[::-1]:
        s = unshuffle(s)
        s = s[l-k:] + s[:l-k]
        s = unshift(s, key)

    return s


def scrambled_cksum(scrambled, width, height, ignore_chars=BLACKSQUARE, encoding=ENCODING):
    """Calculate the checksum for a scrambled solution."""
    data = replace_chars(square(scrambled, width, height), ignore_chars)
    return data_cksum(data.encode(encoding, ENCODING_ERRORS))


def key_digits(key):
    """Split a numeric key into a list of its digits."""
    return [int(c) for c in str(key).zfill(4)]


def square(data, w, h):
    """
    Transpose the grid data (column-major to row-major or vice-versa).
    
    Across Lite uses column-major order for scrambling.
    """
    aa = [data[i:i+w] for i in range(0, len(data), w)]
    return ''.join(
        [''.join([aa[r][c] for r in range(0, h)]) for c in range(0, w)]
    )


def shift(s, key):
    """Caesar-shift characters in s based on key digits."""
    atoz = string.ascii_uppercase
    return ''.join(
        atoz[(atoz.index(c) + key[i % len(key)]) % len(atoz)]
        for i, c in enumerate(s)
    )


def unshift(s, key):
    """Reverse Caesar-shift characters in s."""
    return shift(s, [-k for k in key])


def shuffle(s):
    """Interleave the two halves of a string (like shuffling a deck of cards)."""
    mid = int(math.floor(len(s) / 2))
    items = functools.reduce(operator.add, zip(s[mid:], s[:mid]))
    return ''.join(items) + (s[-1] if len(s) % 2 else '')


def unshuffle(s):
    """Reverse the shuffle operation."""
    return s[1::2] + s[::2]


def restore(s, t):
    """
    Restore black squares from a source string s into a cleaned string t.

    Example:
    >>> restore('ABC.DEF', 'XYZABC')
    'XYZ.ABC'
    """
    t_iter = (c for c in t)
    return ''.join(next(t_iter) if not is_blacksquare(c) else c for c in s)


def is_blacksquare(c):
    """Check if a character represents a black square."""
    if isinstance(c, int):
        c = chr(c)
    return c in [BLACKSQUARE, BLACKSQUARE2]


#
# functions for parsing / serializing primitives
#


def parse_bytes(s):
    """Convert a bytes object into a list of integers."""
    return list(struct.unpack('B' * len(s), s))


def pack_bytes(a):
    """Convert a list of integers into a bytes object."""
    return struct.pack('B' * len(a), *a)


def parse_dict(s):
    """
    Parse a dictionary from a string format: k1:v1;k2:v2;...
    """
    return dict(p.split(':') for p in s.split(';') if ':' in p)


def dict_to_string(d):
    """
    Convert a dictionary to a string format: k1:v1;k2:v2;...;
    """
    return ';'.join(':'.join(map(str, [k, v])) for k, v in d.items()) + ';'
