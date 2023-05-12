import fontforge
import os.path
import psMat
import sys
import unicodedata
from math import tan, pi

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

import utils
import utils_ui
import utils_cv

def ContourInContour(small_contour, big_contour):
    bb = small_contour.boundingBox()
    BB = big_contour.boundingBox()
    return bb[0] > BB[0] and bb[1] > BB[1] and bb[2] < BB[2] and bb[3] < BB[3]

# Copy glyph between fonts
def CopyGlyph(code, source_font, target_font, copy_width=True):
    glyph_name = fontforge.nameFromUnicode(code)
    if glyph_name not in source_font or not source_font[glyph_name].isWorthOutputting():
        return False

    target_char = target_font.createChar(code)
    target_char.clear()

    source_glyph = source_font[glyph_name]

    # If source glyph contains references, create a temporary copy with
    # dereferenced contours. Another possible approach is copying reference
    # glyphs to target first, but we prefer not to clutter the target font.
    deref = False
    if source_glyph.references:
        changed = source_font.changed

        # Make temporary copy in the source font.
        deref_glyph = source_font.createChar(-1, "temporary")
        pen = deref_glyph.glyphPen()
        source_glyph.draw(pen)
        pen = None

        # Unlink refs in temporary copy to make contours available
        deref_glyph.unlinkRef()
        source_glyph = deref_glyph
        deref = True

    pen = target_char.glyphPen()
    source_glyph.draw(pen)
    pen = None

    if deref:
        source_font.removeGlyph(deref_glyph)
        source_font.changed = changed

    target_char.glyphname = glyph_name
    if copy_width:
        target_char.width = source_font[glyph_name].width

    return True

# Collect glyph contours including references. Output contours are sorted by
# enclosed area with smaller area first.
def Contours(glyph):
    def contour_area(contour):
        bb = contour.boundingBox()
        return (bb[2] - bb[0]) * (bb[3] - bb[1])

    # Collect reference contours
    ref_contours = (tuple(glyph.font[ref_name].foreground) for ref_name, _, _ in glyph.references)
    ref_contours = tuple(ref_contours)

    contours = sum(ref_contours, ()) + tuple(glyph.foreground)

    # Sort contous by size of bounding box
    contours = sorted(contours, key=lambda c: contour_area(c))

    # Remove contours fully enclosed inside other contours, they are not
    # representative of either accent or body position
    for i in reversed(range(len(contours))):
        # Remove contour i if it's fully inside some bigger contour
        for j in range(i + 1, len(contours)):
            if ContourInContour(contours[i], contours[j]):
                contours.pop(i)
                break

    return contours

def UnslantedBoundingBox(glyph):
    # Assume that the glyph bounding box is determined by the largest contour
    largest_contour = Contours(glyph)[-1]
    uns_contour = utils.Unslant(largest_contour, glyph.font.italicangle)

    return uns_contour.boundingBox()

def HasAscender(char):
    return char in "bdfhkltṭ"

def ShrinkToCedilla(glyph):
    target_accent = glyph.foreground[0]

    # Cedilla root points are the ones nearest to the zero baseline
    pts = (pt for pt in target_accent if pt.on_curve)
    pts = sorted(pts, key=lambda pt: abs(pt.y))
    pt_root1, pt_root2 = pts[0], pts[1]

    # Delete everything above both root points
    level = max(pt_root1.y, pt_root2.y)
    for i in reversed(range(len(target_accent))):
        if target_accent[i].y > level and target_accent[i].on_curve:
            del target_accent[i]
    
    # The resulting contour is still detached from the glyph, we
    # must draw it back.
    pen = glyph.glyphPen()
    target_accent.draw(pen)
    pen = None

    # Compute accent root for proper anchoring
    return (pt_root1.x + pt_root2.x) / 2

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
    # Accented characters which can be represented by a single Unicode glyph
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

    # Special non-latin characters
    special = [0x02BE, # right half ring
               0x02BF, # left half ring
               0x00B0, # degree sign
               0x0259, # small letter schwa
               0x018F, # capital letter schwa - optional
               0x014B, # small letter eng
               0x014A  # capital letter eng
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

    return chars, seqs, special

def BuildRomanization(unused, font):
    latin_font = SelectLatinFont()

    if (latin_font is None):
        return

    for lookup in ("UpperAccent", "LowerAccent"):
        if lookup in font.gpos_lookups:
            font.removeLookup(lookup)
        font.addLookup(lookup, "gpos_mark2base", None, (("mark",(("latn",("dflt")),)),))
        font.addLookupSubtable(lookup, lookup)
        font.addAnchorClass(lookup, lookup)

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

    chars, seqs, special = RomanizationCodes()

    for code in chars:
        MakeAccentedCharacter(latin_font, font, code)

    for code in special:
        CopyGlyph(code, latin_font, font)

    if "uni0259" not in font:
        BuildSmallSchwa(font)

    BuildHalfRings(font)
    AddBaseAnchors(font)

    font.mergeFeature(script_dir + "/Latin.fea")

def MakeLowerAccent(accent_name, source_font,
                    source_ref_name, target_font, option=None):
    code = fontforge.unicodeFromName(accent_name)

    if not CopyGlyph(code, source_font, target_font, copy_width=False):
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
            cedilla_root = ShrinkToCedilla(target_glyph)

        # Move accent to the lower position (negative delta)
        delta_y = src_body.boundingBox()[1] - src_accent.boundingBox()[3] - descending_dist
        target_glyph.transform(psMat.translate(0, delta_y))

        if option == "cedilla":
            x_shift = -cedilla_root
        else:
            # center the resulting glyph
            uns_bb = UnslantedBoundingBox(target_glyph)
            x_shift = - (uns_bb[0] + uns_bb[2]) / 2

        target_glyph.transform(psMat.translate(x_shift, 0))
        target_glyph.width = 0

        target_glyph.glyphname = accent_name

    # Add anchor point to the accent
    target_glyph.addAnchorPoint("LowerAccent", "mark", 0, 0)

def MakeUpperAccent(accent_name, source_font,
                    src_cap_ref_name, src_small_ref_name,
                    target_font, option=None):
    code = fontforge.unicodeFromName(accent_name)

    if not CopyGlyph(code, source_font, target_font, copy_width=False):
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
        uns_bb = UnslantedBoundingBox(target_glyph)
        x_shift = - (uns_bb[0] + uns_bb[2]) / 2
        target_glyph.transform(psMat.translate(x_shift, 0))
        target_glyph.width = 0

        target_glyph.glyphname = accent_name

    # Add anchor point to the accent
    target_glyph.addAnchorPoint("UpperAccent", "mark", 0, 0)

def CharNames(norm):
    base_code = ord(norm[0])
    accent_codes = [ord(norm_c) for norm_c in norm[1:]]
    base_name = fontforge.nameFromUnicode(base_code)
    accent_names = [fontforge.nameFromUnicode(code)for code in accent_codes]

    return base_name, accent_names

def ComputeAccentShifts(font, norm):
    base_name, accent_names = CharNames(norm)
    x_height = font["x"].boundingBox()[3]

    # Horizontal accent position
    uns_base_bb = UnslantedBoundingBox(font[base_name])
    x_lower_accent = (uns_base_bb[2] + uns_base_bb[0]) / 2
    x_upper_accent = x_lower_accent

    # For small characters with ascenders, place the accent over the ascender
    if HasAscender(norm[0]):
        base_contour = Contours(font[base_name])[-1]
        uns_base_contour = utils.Unslant(base_contour, font.italicangle)
        true_points = [(p.x, p.y) for p in uns_base_contour if p.on_curve]
        x_upper_accent = utils_cv.AscenderMeanX(true_points, x_height)

    # Vertical accent position
    xy_accents = []
    for accent_name in accent_names:
        y_accent = 0
        if norm[0].isupper() or HasAscender(norm[0]):
            ascending_dist = utils.GetGlyphCommentProperty(font[accent_name], "AscenderShift")
            if ascending_dist is not None:
                y_accent = ascending_dist

        # Check accent position relative to the baseline
        is_lower_accent = (font[accent_name].boundingBox()[1] < 0)
        x_accent = x_lower_accent if is_lower_accent else x_upper_accent

        x_accent -= y_accent * tan(font.italicangle * pi / 180)

        xy_accents.append([x_accent, y_accent, is_lower_accent])

    # Stack upper accents if necessary
    if (len(accent_names) == 2 and not xy_accents[0][2] and not xy_accents[1][2]):
        contour1 = [(p.x, p.y) for p in Contours(font[accent_names[0]])[0]]
        contour2 = [(p.x, p.y) for p in Contours(font[accent_names[1]])[0]]
        shift = utils_cv.StackAccents(contour1, contour2, x_height / 10)

        # shift the second accent up as appropriate
        xy_accents[1][1] += shift
        xy_accents[1][0] -= shift * tan(font.italicangle * pi / 180)

    return xy_accents

def ShiftAccentsX(glyph, y_shift):
    unistr = chr(glyph.unicode)
    norm = unicodedata.normalize("NFD", unistr)
    base_name, _ = CharNames(norm)

    base_glyph = glyph.font[base_name]
    base_bb = base_glyph.boundingBox()

    # Copy foreground layer
    l = glyph.layers[1]

    # Transform accent contours only
    trf = psMat.translate(0, y_shift)
    for c in l:
        if c.boundingBox()[1] < base_bb[1] - 1 or c.boundingBox()[3] > base_bb[3] + 1:
            c.transform(trf)

    pen = glyph.glyphPen()
    l.draw(pen)
    pen = None
    glyph.width = base_glyph.width

def MakeAccentedCharacter(latin_font, font, code):
    unistr = chr(code)

    # Call recursively for upper-case character
    if unistr.islower():
        MakeAccentedCharacter(latin_font, font, ord(unistr.upper()))

    if CopyGlyph(code, latin_font, font):
        return

    # Get Unicode components by canonical decomposition
    norm = unicodedata.normalize("NFD", unistr)
    base_name, accent_names = CharNames(norm)

    xy_accents = ComputeAccentShifts(font, norm)

    # Initialize target character
    target_char = font.createChar(code)
    target_char.clear()
    pen = target_char.glyphPen()

    # Add references to the base character and to the accent
    pen.addComponent(base_name, psMat.identity())
    for accent_name, xy_accent in zip(accent_names, xy_accents):
        pen.addComponent(accent_name, psMat.translate(*xy_accent[:2]))
    pen = None

    target_char.width = font[base_name].width
    target_char.glyphname = fontforge.nameFromUnicode(code)

def BuildSmallSchwa(font):
    schwa_code = 0x0259
    schwa_char = font.createChar(schwa_code)
    schwa_char.clear()

    pen = schwa_char.glyphPen()
    font["e"].draw(pen)
    pen = None

    bb_e = font["e"].boundingBox()
    schwa_char.transform(psMat.rotate(3.1415))
    schwa_char.transform(psMat.translate(bb_e[0] + bb_e[2], bb_e[1] + bb_e[3]))

    schwa_char.glyphname = fontforge.nameFromUnicode(schwa_code)
    schwa_char.width = font["e"].width

    return True

def CopyAndCutout(source_char, target_char, cutting_bb):
    target_char.clear()

    # Copy ring into half ring
    pen = target_char.glyphPen()
    source_char.draw(pen)

    # Draw rectangle over the cutting bounding box
    pen.moveTo((cutting_bb[0], cutting_bb[1]))
    pen.lineTo((cutting_bb[0], cutting_bb[3]))
    pen.lineTo((cutting_bb[2], cutting_bb[3]))
    pen.lineTo((cutting_bb[2], cutting_bb[1]))
    pen.closePath()                       # end the contour
    pen = None

    # Build half-ring contour by intersection
    target_char.intersect()
    target_char.left_side_bearing = source_char.left_side_bearing
    target_char.right_side_bearing = source_char.right_side_bearing

def BuildHalfRings(font):
    # We expect some ring to be there
    ring_char = None
    if "degree" in font:
        ring_char = font["degree"]
    elif "ring" in font:
        ring_char = font["ring"]
    elif "uni030A" in font:
        ring_char = font["uni030A"] # combining ring above

    if ring_char is None:
        return

    ring_bb = ring_char.boundingBox()

    # Copy ring and keep the left half
    left_half_ring_char = font.createChar(0x02BF)

    left_half_bb = (ring_bb[0] - 1, ring_bb[1] - 1,
                    (ring_bb[0] + ring_bb[2]) / 2, ring_bb[3] + 1)

    CopyAndCutout(ring_char, left_half_ring_char, left_half_bb)

    # Copy ring and keep the right half
    right_half_ring_char = font.createChar(0x02BE)
    
    right_half_bb = ((ring_bb[0] + ring_bb[2]) / 2, ring_bb[1] - 1,
                     ring_bb[2] + 1, ring_bb[3] + 1)

    CopyAndCutout(ring_char, right_half_ring_char, right_half_bb)

def AddBaseAnchors(font):
    upper_accent = "acutecomb"
    lower_accent = "dotbelowcomb"

    # All the standard latin letters need anchors
    base_codes = list(range(ord('a'), ord('z') + 1)) + list(range(ord('A'), ord('Z') + 1))

    # T with dow below and T with dot above need anchors too (for placing the other dot)
    base_codes.extend([0x1E6A, 0x1E6B, 0x1E6C, 0x1E6D])

    for accent_name in (upper_accent, lower_accent):
        for base_code in base_codes:
            accent_code = fontforge.unicodeFromName(accent_name)
            base_name = fontforge.nameFromUnicode(base_code)

            norm = chr(base_code) + chr(accent_code)
            xy_accents = ComputeAccentShifts(font, norm)

            is_lower_accent = (font[accent_name].boundingBox()[1] < 0)
            lookup = "LowerAccent" if is_lower_accent else "UpperAccent"

            # Add anchor point to the base char according to the accent type
            font[base_name].addAnchorPoint(lookup, "base", *xy_accents[0])
