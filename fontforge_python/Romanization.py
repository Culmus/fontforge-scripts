import fontforge
import os.path
import psMat
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

import utils_ui

# Copy glyph between fonts
def CopyGlyph(code, source_font, target_font):
    glyph_name = fontforge.nameFromUnicode(code)
    target_char = target_font.createChar(code)
    target_char.clear()

    pen = target_char.glyphPen()
    source_font[glyph_name].draw(pen)
    pen = None

    target_char.glyphname = glyph_name

def Contours(glyph):
    def contour_area(contour):
        bb = contour.boundingBox()
        return (bb[2] - bb[0]) * (bb[3] - bb[1])

    # Sort contous by size of bounding box
    return sorted(glyph.foreground, key=lambda c: contour_area(c))

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

    if (latin_font is None):
        return

    MakeLowerDot(latin_font, font)

    # TODO: build romanization support glyphs

def MakeLowerDot(source_font, target_font):
    code = fontforge.unicodeFromName("dotbelowcomb")

    if "dotbelowcomb" in source_font and source_font["dotbelowcomb"].isWorthOutputting():
        CopyGlyph(code, source_font, target_font)
    else:
        # Use "i dieresis" as a reference glyph
        i_contours = Contours(source_font["idieresis"])
        i_dot = i_contours[0]
        i_body = i_contours[-1]

        # Distance between the lower dot and the baseline
        descending_dist = i_dot.boundingBox()[1] - i_body.boundingBox()[3]

        # Reset target glyph
        target_glyph = target_font.createChar(code)
        target_glyph.clear()

        # Copy dot from i_dieresis
        pen = target_glyph.glyphPen()
        i_dot.draw(pen)
        pen = None

        # Move dot to the lower position (negative delta)
        delta_y = - i_dot.boundingBox()[3] - descending_dist
        target_glyph.transform(psMat.translate(0, delta_y))

        # center the resulting glyph
        bb = target_glyph.boundingBox()
        target_glyph.left_side_bearing = (bb[0] - bb[2]) / 2
        target_glyph.width = 0

        target_glyph.glyphname = "dotbelowcomb"
