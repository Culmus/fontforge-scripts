import fontforge
import os.path
import psMat
import sys
import unicodedata

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

import utils
import utils_ui

def ContourInContour(small_contour, big_contour):
    bb = small_contour.boundingBox()
    BB = big_contour.boundingBox()
    return bb[0] > BB[0] and bb[1] > BB[1] and bb[2] < BB[2] and bb[3] < BB[3]

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
        # Remove contour i if it's fully inside some bigger contour
        for j in range(i + 1, len(contours)):
            if ContourInContour(contours[i], contours[j]):
                contours.pop(i)
                break

    return contours

def HasAscender(char):
    return char in "bdfhklt"

def ShrinkToCedilla(glyph):
    target_accent = glyph.foreground[0]

    # Cedilla root points are the ones nearest to the zero baseline
    pts = (pt for pt in target_accent if pt.on_curve)
    pts = sorted(pts, key=lambda pt: abs(pt.y))
    pt_root1, pt_root2 = pts[0], pts[1]

    # Delete everything above the root points
    for i in reversed(range(len(target_accent))):
        if target_accent[i].y > pt_root2.y and target_accent[i].on_curve:
            del target_accent[i]
    
    # The resulting contour is still detached from the glyph, we
    # must draw it back.
    pen = glyph.glyphPen()
    target_accent.draw(pen)
    pen = None

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

def RomanizationCodes():
    # Romanization characters which can be represented by a single Unicode glyph
    chars = [0x1E25, # h + lower dot
             0x1E6D, # t + lower dot
             0x1E63, # s + lower dot
             0x015B, # s acute
             0x0161, # s caron
             0x00E5, # a ring
             0x0229, # e cedille
             0x0175, # w circumflex
             0x0103, # a breve
             0x014F, # o breve
             0x1E1D, # e cedilla breve
             0x00E2, # a circumflex
             0x014D, # o macron
             0x00E9, # e acute
             0x016B, # u macron
             0x1E33  # k + lower dot
    ]

    # Romanization characters which don't have a single Unicode glyph
    seqs = [[0x0073, 0x0300], # s grave
            [0x0073, 0x0300, 0x0307], # s grave + upper dot
            [0x0062, 0x0331] # b lower macron
    ]

    # Add consonants with dagesh (upper dot)
    consonants = "bgdhwzṭyklmnspṣqrśšt" # contains Unicode characters
    for c in consonants:
        # Combine consonant with upper dot and add to the list
        norm = unicodedata.normalize("NFD", c)
        code = unicodedata.normalize("NFC", norm + "\u0307")
        if len(code) == 1:
            chars.append(ord(code))
        else:
            seqs.append([ord(ch) for ch in code])

    return chars, seqs

def BuildRomanization(unused, font):
    latin_font = SelectLatinFont()

    if (latin_font is None):
        return

    MakeLowerAccent("dotbelowcomb", latin_font, "idieresis", font)
    MakeLowerAccent("uni0331", latin_font, "amacron", font) # "COMBINING MACRON BELOW"
    MakeLowerAccent("uni0327", latin_font, "ccedilla", font, option="cedilla") # "COMBINING CEDILLA"

    MakeUpperAccent("acutecomb", latin_font, "Sacute", "sacute", font)
    MakeUpperAccent("gravecomb", latin_font, "Ograve", "ograve", font)
    MakeUpperAccent("uni0302", latin_font, "Acircumflex", "acircumflex", font) # "COMBINING CIRCUMFLEX ACCENT"
    MakeUpperAccent("uni0304", latin_font, "Amacron", "amacron", font) # "COMBINING MACRON"
    MakeUpperAccent("uni0306", latin_font, "Abreve", "abreve", font) # "COMBINING BREVE"
    MakeUpperAccent("uni0307", latin_font, "Edotaccent", "edotaccent", font) # "COMBINING DOT ABOVE"
    MakeUpperAccent("uni030C", latin_font, "Zcaron", "zcaron", font) # "COMBINING CARON"
    MakeUpperAccent("uni030A", latin_font, "Aring", "aring", font, option="ring") # "COMBINING RING ABOVE"

    chars, seqs = RomanizationCodes()

    for code in chars:
        MakeAccentedCharacter(font, code)

    # TODO: build more romanization support glyphs

def MakeLowerAccent(accent_name, source_font,
                    source_ref_name, target_font, option=None):
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

        # The cedilla is connected to the glyph, so they were copied together.
        # We need to delete the glyph and leave just the cedilla itself
        if option == "cedilla":
            ShrinkToCedilla(target_glyph)

        # Move accent to the lower position (negative delta)
        delta_y = src_body.boundingBox()[1] - src_accent.boundingBox()[3] - descending_dist
        target_glyph.transform(psMat.translate(0, delta_y))

        # center the resulting glyph
        bb = target_glyph.boundingBox()
        target_glyph.left_side_bearing = (bb[0] - bb[2]) / 2
        target_glyph.width = 0

        target_glyph.glyphname = accent_name

def MakeUpperAccent(accent_name, source_font,
                    src_cap_ref_name, src_small_ref_name,
                    target_font, option=None):
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

        # Complete ring inner contour
        if (option == "ring"):
            # Find the contour inside src_accent
            src_accent2 = next((c
                                for c
                                in source_font[src_small_ref_name].foreground
                                if ContourInContour(c, src_accent)), None)
            src_accent2.draw(pen)

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

    # Call recursively for upper-case character
    if unistr.islower():
        MakeAccentedCharacter(font, ord(unistr.upper()))

    # Get Unicode components by canonical decomposition
    norm = unicodedata.normalize("NFD", unistr)
    base_code = ord(norm[0])
    accent_code = ord(norm[1])
    base_name = fontforge.nameFromUnicode(base_code)
    accent_name = fontforge.nameFromUnicode(accent_code)

    # Horizontal accent position
    base_bb = font[base_name].boundingBox()
    x_accent = (base_bb[2] + base_bb[0]) / 2

    # Vertical accent position
    y_accent = 0
    if unistr.isupper() or HasAscender(norm[0]):
        ascending_dist = utils.GetGlyphCommentProperty(font[accent_name], "AscenderShift")
        if ascending_dist is not None:
            y_accent = ascending_dist;

    # Initialize target character
    target_char = font.createChar(code)
    target_char.clear()
    pen = target_char.glyphPen()

    # Add references to the base character and to the accent
    pen.addComponent(base_name, psMat.identity())
    pen.addComponent(accent_name, psMat.translate(x_accent, y_accent))
    pen = None

    target_char.width = font[base_name].width
    target_char.glyphname = fontforge.nameFromUnicode(code)
