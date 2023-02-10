import fontforge
import os.path
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

import utils_ui

# Ask user to select a source font for latin glyphs among the currently
# opened fonts.

def SelectLatinFont():
    loaded_fonts = fontforge.fonts()
    loaded_names = tuple((f.fullname for f in loaded_fonts))

    result = utils_ui.RadioUI("Select Latin Font", loaded_names, 0)

    if result is not -1:
        latin_font = loaded_fonts[result]
    else:
        latin_font = None

    return latin_font

def BuildRomanization(unused, font):
    latin_font = SelectLatinFont()

    # TODO: build romanization support glyphs
