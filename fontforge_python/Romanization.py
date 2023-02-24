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

def BuildRomanization(unused, font):
    latin_font = SelectLatinFont()

    if (latin_font is None):
        return

    MakeLowerAccent("dotbelowcomb", latin_font, "idieresis", font)
    MakeLowerAccent("uni0331", latin_font, "amacron", font) # "COMBINING MACRON BELOW"
    MakeLowerAccent("uni0327", latin_font, "ccedilla", font, option="cedilla") # "COMBINING CEDILLA"

    MakeUpperAccent("acutecomb", latin_font, "Sacute", "sacute", font)
    MakeUpperAccent("gravecomb", latin_font, "Ograve", "ograve", font)
    MakeUpperAccent("uni0304", latin_font, "Amacron", "amacron", font) # "COMBINING MACRON"
    MakeUpperAccent("uni0306", latin_font, "Abreve", "abreve", font) # "COMBINING BREVE"
    MakeUpperAccent("uni0307", latin_font, "Edotaccent", "edotaccent", font) # "COMBINING DOT ABOVE"
    MakeUpperAccent("uni030C", latin_font, "Zcaron", "zcaron", font) # "COMBINING CARON"
    MakeUpperAccent("uni030A", latin_font, "Aring", "aring", font, option="ring") # "COMBINING RING ABOVE"

    code = 0x1E25 # h + lower dot
    MakeAccentedCharacter(font, code)

    code = 0x1E6D # t + lower dot
    MakeAccentedCharacter(font, code)

    code = 0x1E63 # s + lower dot
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
