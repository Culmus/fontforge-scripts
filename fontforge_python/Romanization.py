import fontforge
import os.path
import psMat
import sys
import unicodedata

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

import utils
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
    contours = sorted(glyph.foreground, key=lambda c: contour_area(c))

    # Remove contours fully enclosed inside other contours, they are not
    # representative of either accent or body position
    for i in reversed(range(len(contours))):
        bb = contours[i].boundingBox()
        # Remove contour i if it's fully inside some bigger contour
        for j in range(i + 1, len(contours)):
            BB = contours[j].boundingBox()
            if bb[0] > BB[0] and bb[1] > BB[1] and bb[2] < BB[2] and bb[3] < BB[3]:
                contours.pop(i)
                break

    return contours

# Ask user to select a source font for latin glyphs among the currently
# opened fonts.

def SelectLatinFont():
    loaded_fonts = fontforge.fonts()
    loaded_names = tuple((f.fullname for f in loaded_fonts))

    result = utils_ui.RadioUI("Select Latin Font", loaded_names, 0)

    if result != -1:
        latin_font = loaded_fonts[result]
    else:
        latin_font = None

    return latin_font

def BuildRomanization(unused, font):
    latin_font = SelectLatinFont()

    if (latin_font is None):
        return

    MakeLowerAccent("dotbelowcomb", latin_font, "idieresis", font)
    MakeLowerAccent("uni0331", latin_font, "amacron", font) # "COMBINING MACRON BELOW"
    MakeUpperAccent("acutecomb", latin_font, "Sacute", "sacute", font)

    code = 0x1E25 # h + lower dot
    MakeAccentedCharacter(font, code)

    code = 0x1E6D # t + lower dot
    MakeAccentedCharacter(font, code)

    code = 0x1E63 # s + lower dot
    MakeAccentedCharacter(font, code)

    # TODO: build more romanization support glyphs

def MakeLowerAccent(accent_name, source_font, source_ref_name, target_font):
    code = fontforge.unicodeFromName(accent_name)

    if accent_name in source_font and source_font[accent_name].isWorthOutputting():
        CopyGlyph(code, source_font, target_font)
    else:
        # Extract elements from the reference glyph
        src_contours = Contours(source_font[source_ref_name])
        src_accent = src_contours[0]
        src_body = src_contours[-1]

        # Distance between the lower accent and the glyph
        descending_dist = src_accent.boundingBox()[1] - src_body.boundingBox()[3]

        # Reset target glyph
        target_glyph = target_font.createChar(code)
        target_glyph.clear()

        # Copy accent from source glyph
        pen = target_glyph.glyphPen()
        src_accent.draw(pen)
        pen = None

        # Move accent to the lower position (negative delta)
        delta_y = src_body.boundingBox()[1] - src_accent.boundingBox()[3] - descending_dist
        target_glyph.transform(psMat.translate(0, delta_y))

        # center the resulting glyph
        bb = target_glyph.boundingBox()
        target_glyph.left_side_bearing = (bb[0] - bb[2]) / 2
        target_glyph.width = 0

        target_glyph.glyphname = accent_name

def MakeUpperAccent(accent_name, source_font,
                    src_cap_ref_name, src_small_ref_name, target_font):
    code = fontforge.unicodeFromName(accent_name)

    if accent_name in source_font and source_font[accent_name].isWorthOutputting():
        CopyGlyph(code, source_font, target_font)
    else:
        # Extract elements from the small reference glyph
        src_contours = Contours(source_font[src_small_ref_name])
        src_accent = src_contours[0]
        src_body = src_contours[-1]

        # Reset target glyph
        target_glyph = target_font.createChar(code)
        target_glyph.clear()

        # Copy accent from source glyph
        pen = target_glyph.glyphPen()
        src_accent.draw(pen)
        pen = None

        # Distance between the location of the upper accent in capital vs small reference
        src_cap_contours = Contours(source_font[src_cap_ref_name])
        src_cap_accent = src_cap_contours[0]
        ascending_dist = src_cap_accent.boundingBox()[1] - src_accent.boundingBox()[1]
        utils.SetGlyphCommentProperty(target_glyph, "AscenderShift", ascending_dist)

        # center the resulting glyph
        bb = target_glyph.boundingBox()
        target_glyph.left_side_bearing = (bb[0] - bb[2]) / 2
        target_glyph.width = 0

        target_glyph.glyphname = accent_name

def MakeAccentedCharacter(font, code):
    unistr = chr(code)

    # Get Unicode components by canonical decomposition
    norm = unicodedata.normalize("NFD", unistr)
    base_code = ord(norm[0])
    accent_code = ord(norm[1])
    base_name = fontforge.nameFromUnicode(base_code)
    accent_name = fontforge.nameFromUnicode(accent_code)

    # Horizontal accent position
    base_bb = font[base_name].boundingBox()
    x_accent = (base_bb[2] + base_bb[0]) / 2

    # Initialize target character
    target_char = font.createChar(code)
    target_char.clear()
    pen = target_char.glyphPen()

    # Add references to the base character and to the accent
    pen.addComponent(base_name, psMat.identity())
    pen.addComponent(accent_name, psMat.translate(x_accent, 0))
    pen = None

    target_char.width = font[base_name].width
    target_char.glyphname = fontforge.nameFromUnicode(code)
