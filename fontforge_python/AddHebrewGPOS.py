import fontforge
import os.path
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

import InitHebrewGlyphData
import AddHebrewContextualGPOS
import utils

# This script for FontForge was created by Maxim Iorsh in 2017. It is public
# domain. You can use it in any way and for any purpose.
# 
# This script automatically generates anchor positions for diacritics from
# neutral data stored in glyph comments.
# 
# The comments stored in a glyph must be in the following format:
# %<anchor-class>=<offset>
# 
# <anchor-class> can be one of vowel equivalence classes (see InitHebrewGlyphData.py).
# <offset> is the horyzontal offset of the anchor from the zero position. In
# Hebrew all diacritics are lined up, and they can't have non-zero vertical
# offset (with the exception of dagesh, which is treated separately).
# 
# For example, a comment in the form "%DiaToBase1=180" means that the anchor for
# hiriq and shwa is located at the point (180,0) in the corresponding glyph.
# The same anchor in the diacritic is always located at (0,0).
# 
# This script was developed and tested with build 20120731.
# Script version: 20 Nov 2017.

def AddHebrewGPOS(unused, font):
    FixLegacyComments(font)

    # Cleanup old lookups
    lookups = font.gpos_lookups

    for l in lookups:
        # Custom persistent lookups shall start with '_', leave them as is.
        if l[0] == "_":
            continue

        # Don't touch kerning
        if font.getLookupInfo(l)[0] == "gpos_pair":
            continue

        font.removeLookup(l, True)

    # Set for each diacritic its appropriate anchor
    for vowel_class, vowels in InitHebrewGlyphData.GetVowelEquiv().items():

        # Create anchor classes in separate lookups
        font.addLookup(vowel_class, "gpos_mark2base", ("right_to_left"), (("mark",(("hebr",("dflt")),)),))
        font.addLookupSubtable(vowel_class, vowel_class)
        font.addAnchorClass(vowel_class, vowel_class)

        # Add anchor points to the diacritics
        for vowel in vowels:
            font[vowel].addAnchorPoint(vowel_class, "mark", 0, 0)

    for glyph_class in InitHebrewGlyphData.GetGlyphEquiv():
        for vowel_class in InitHebrewGlyphData.GetVowelEquiv():

            # For each glyph class vs. diacritic class we retrieve the
            # anchor position from the comments on the glyph.
            (anchor_pos, basewidth) = utils.GetClassProperty(font, glyph_class, vowel_class)

            if anchor_pos is None:
                continue

            # Set the appropriate anchor for all members of glyph equivalence class
            for glyph in glyph_class:
                if glyph in font:

                    # Fix for glyphs whose width was modified by dagesh
                    anchor_fix = font[glyph].width - basewidth

                    font[glyph].addAnchorPoint(vowel_class, "base", anchor_pos + anchor_fix, 0)

    # Special processing for dagesh

    font.selection.select(("ranges",), "uniFB30","uniFB4A")
    font.selection.select(("more",), "uniE805") # Alternative ayin with dagesh - private use area

    for glyph in font.selection.byGlyphs:

        # Find the dagesh reference transformation
        dagesh_ref_trf = next(ref[1] for ref in glyph.references if ref[0] == "afii57807")

        # Find the base glyph
        if (glyph.glyphname == "uniE805"):
            base = font["uniFB20"]
        else:
            base_unicode = glyph.unicode - 62816
            base = font[fontforge.nameFromUnicode(base_unicode)]

        base.addAnchorPoint("DiaToBaseD", "base", dagesh_ref_trf[4], dagesh_ref_trf[5])

    AddHebrewContextualGPOS.AddHebrewContextualGPOS(unused, font)

def FixLegacyComments(font):
    # Check if an old comment is present
    old_rafe = (utils.GetGlyphCommentProperty(font["afii57664"], "RafeToBase") is not None)

    if old_rafe:
        for glyph in font:
            c = utils.GetGlyphCommentProperty(font[glyph], "RafeToBase")
            if c is not None:
                utils.SetGlyphCommentProperty(font[glyph], "UpperToBase", c)
                utils.SetGlyphCommentProperty(font[glyph], "RafeToBase", None)
