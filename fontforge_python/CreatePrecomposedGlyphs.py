import fontforge
import psMat
import os.path
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

import InitHebrewGlyphData
import utils

# Build composite character (e.g. Yiddish ligature) from two base characters
def AddConsonantCouple(font, right, left, result):

    font[result].clear()

    pen = font[result].glyphPen()
    pen.addComponent(left, psMat.identity())
    pen.addComponent(right, psMat.translate(font[left].width, 0))
    pen = None

    font[result].width = font[left].width + font[right].width

# Build composite character (e.g. Aleph-qamats) from consonant and vowel
def AddConsonantVowel(font, consonant, vowel, result):

    font[result].clear()

    # Retrieve the vowel location from comments
    vowel_equiv_items = InitHebrewGlyphData.GetVowelEquiv().items()
    vowel_class = next((key for key, value in vowel_equiv_items if (vowel in value)))
    anchor_pos = utils.GetGlyphCommentProperty(font[consonant], vowel_class)

    if anchor_pos is None:
        anchor_pos = 0

    pen = font[result].glyphPen()
    pen.addComponent(consonant, psMat.identity())
    pen.addComponent(vowel, psMat.translate(anchor_pos, 0))
    pen = None

    font[result].width = font[consonant].width
    font[result].useRefsMetrics(consonant)

# Build narrow version of hataf glyph from existing hataf-meteg glyph
def AddNarrowHataf(font, hataf_meteg, narrow_hataf):

    narrow_hataf_glyph = font.createChar(-1, narrow_hataf)
    narrow_hataf_glyph.clear()

    # Sort hataf-meteg components by position from left to right. Thus the two shwa contours
    # will be at the end of the sorted list, preceded by the meteg
    source_contours = font[hataf_meteg].foreground.dup()
    source_contours = sorted(source_contours, key=lambda c: c.boundingBox()[2], reverse=False)

    # Compute shwa displacement (distance between it and the meteg). Consider both shwa dots
    # to address possible slanting.
    shwa_displacement = (source_contours[-1].boundingBox()[0] + source_contours[-2].boundingBox()[2] -
        source_contours[-3].boundingBox()[0] - source_contours[-3].boundingBox()[2]) / 2

    # delete meteg
    del source_contours[-3]

    # move shwa to meteg's place
    source_contours[-1].transform(psMat.translate(-shwa_displacement, 0))
    source_contours[-2].transform(psMat.translate(-shwa_displacement, 0))

    # draw the contours into the narrow hataf
    pen = narrow_hataf_glyph.glyphPen()
    for contour in source_contours:
        contour.draw(pen)
    pen = None

    # center the resulting glyph
    bb = narrow_hataf_glyph.boundingBox()
    narrow_hataf_glyph.left_side_bearing = (bb[0] - bb[2]) / 2
    narrow_hataf_glyph.width = 0

# Build new glyph by picking specific contours from an existing glyph. The contours are
# specified by index, as if they were sorted left-to-right
def AddByPartialCopy(font, source, target, components):

    target_glyph = font.createChar(-1, target)
    target_glyph.clear()

    # Sort source components by position from left to right.
    source_contours = font[source].foreground.dup()
    source_contours = sorted(source_contours, key=lambda c: c.boundingBox()[2], reverse=False)

    # draw the desired contours into the target
    pen = target_glyph.glyphPen()
    for contour_idx in components:
        source_contours[contour_idx].draw(pen)
    pen = None

    # center the resulting glyphs
    bb = target_glyph.boundingBox()
    target_glyph.left_side_bearing = (bb[0] - bb[2]) / 2
    target_glyph.width = 0

def CreatePrecomposedGlyphs(unused, font):

    CREATE_MISSING = 0
    RECREATE_ALL   = 1
    CANCEL         = 2
    CHOICE_MAP = { CREATE_MISSING : "Create missing",
                   RECREATE_ALL   : "Recreate all",
                   CANCEL         : "Cancel" }

    choice = CREATE_MISSING

    def ToDo(name):
        return (choice == RECREATE_ALL or name not in font or font[name].foreground.isEmpty())

    if any(not ToDo(c) for c in ["hatafsegol.narrow", "hatafpatah.narrow", "hatafqamats.narrow",
                                "segol.narrow", "tsere.narrow", "patah.narrow", "qamats.narrow"]):
        choice = fontforge.ask("", "Some narrow diacritics are present",
                               tuple(value for (key, value) in sorted(CHOICE_MAP.items())),
                               CREATE_MISSING, CANCEL)

    if choice == CANCEL:
        return

    AddConsonantCouple(font, "afii57669", "afii57669", "afii57716") # vav-vav
    AddConsonantCouple(font, "afii57669", "afii57673", "afii57717") # vav-yod
    AddConsonantCouple(font, "afii57673", "afii57673", "afii57718") # yod-yod

    AddConsonantVowel(font, "afii57669", "afii57806", "uniE801") # vav-holam
    AddConsonantVowel(font, "afii57673", "afii57793", "uniFB1D") # yod-hiriq
    AddConsonantVowel(font, "afii57664", "afii57798", "uniFB2E") # aleph-patah
    AddConsonantVowel(font, "afii57664", "afii57797", "uniFB2F") # aleph-qamats
    AddConsonantVowel(font, "afii57665", "afii57841", "uniFB4C") # beth-rafe
    AddConsonantVowel(font, "afii57675", "afii57841", "uniFB4D") # kaf-rafe
    AddConsonantVowel(font, "afii57684", "afii57841", "uniFB4E") # pe-rafe

    # Right-side meteg is identical to the ordinary meteg,
    # but bears different anchors
    AddByPartialCopy(font, "afii57839", "meteg.right", [0])

    if ToDo("hatafsegol.narrow"):
        AddNarrowHataf(font, "uniE806", "hatafsegol.narrow")
    if ToDo("hatafpatah.narrow"):
        AddNarrowHataf(font, "uniE807", "hatafpatah.narrow")
    if ToDo("hatafqamats.narrow"):
        AddNarrowHataf(font, "uniE808", "hatafqamats.narrow")

    if ToDo("segol.narrow"):
        AddByPartialCopy(font, "hatafsegol.narrow", "segol.narrow", [0, 1, 2])
    if ToDo("tsere.narrow"):
        AddByPartialCopy(font, "segol.narrow", "tsere.narrow", [0, 2])
    if ToDo("patah.narrow"):
        AddByPartialCopy(font, "hatafpatah.narrow", "patah.narrow", [0])
    if ToDo("qamats.narrow"):
        AddByPartialCopy(font, "hatafqamats.narrow", "qamats.narrow", [0])
