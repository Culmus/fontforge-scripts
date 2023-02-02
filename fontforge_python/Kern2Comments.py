import fontforge
import os.path
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

import InitHebrewGlyphData
import utils

# For each consonant/vowel pair check whether it is a kerning pair and add an
# appropriate comment to the consonant glyph.

def Kern2Comments(unused, font):

    for glyph_class in InitHebrewGlyphData.GetGlyphEquiv():
        for glyph in glyph_class:

            if glyph not in font:
                print("Missing glyph: " + glyph)
                continue

            # For each consonant build a map: vowel_name => X-kerning
            kernings = {data[2] : data[3] for data in font[glyph].getPosSub("_Diakern") if data[1] == "Pair"}

            for vowel, xkern in kernings.items():
                vowel_class = next((c for c, l in InitHebrewGlyphData.GetVowelEquiv().items() if vowel in l), None)

                if vowel_class is not None:
                    utils.SetGlyphCommentProperty(font[glyph], vowel_class, -xkern)

                    # Reset kerning
                    font[glyph].addPosSub("_Diakern", vowel, 0)

    # "_Diakern" is a dummy kerning table used in UI to facilitate
    # diacritics positioning. It should be cleaned at the end.

    if "_Diakern" in font.gpos_lookups:
        font.removeLookup("_Diakern")

    font.addLookup("_Diakern", "gpos_pair", ("right_to_left"), (("kern",(("hebr",("dflt")),)),))
    font.addLookupSubtable("_Diakern", "_Diakern")
