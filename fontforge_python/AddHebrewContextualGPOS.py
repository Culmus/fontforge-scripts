import fontforge
import math
import os.path
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

import GuessMarkToMarkGaps
import InitHebrewGlyphData
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

def AddHebrewMarkToMarkGPOS(font):

    # Create mark-to-mark anchors

    # Put anchors on the median line of TSERE, to prevent visual mess with mark-to-base anchors
    ylevel = (font["afii57794"].boundingBox()[1] + font["afii57794"].boundingBox()[3]) / 2

    # Set for each diacritic its appropriate mark anchor
    for right_class, vowels in InitHebrewGlyphData.GetVowelRightEquiv().items():

        # Create anchor classes in separate lookups
        # Append the lookup to the end
        font.addLookup(right_class, "gpos_mark2mark", ("right_to_left"), (("mkmk",(("hebr",("dflt")),)),), font.gpos_lookups[-1])
        font.addLookupSubtable(right_class, right_class)
        font.addAnchorClass(right_class, right_class)

        # Add anchor points to the diacritics
        for vowel in vowels:
            bbox = font[vowel].boundingBox()
            font[vowel].addAnchorPoint(right_class, "mark", bbox[2], ylevel)

    for left_class in InitHebrewGlyphData.GetVowelLeftEquiv():
        for right_class in InitHebrewGlyphData.GetVowelRightEquiv():

            # For each left class vs. right class we retrieve the
            # anchor position from the comments on the left class.
            # NOTE: "left class" denotes class of vowels with same left-hand side shape,
            #       which affects the placement when the vowel is positioned on the right.
            # SCHEMA: <right-class-vowel>|----gap----|<left-class-vowel>

            good_vowels = [v for v in left_class if (v in font and utils.GetGlyphCommentProperty(font[v], right_class) is not None)]

            if not good_vowels:
                continue

            # Gap
            gap = utils.GetGlyphCommentProperty(font[good_vowels[0]], right_class)

            # Set the appropriate anchor for all members of left shape vowel equivalence class

            for vowel in left_class:
                if vowel in font:
                    bbox = font[vowel].boundingBox()
                    font[vowel].addAnchorPoint(right_class, "basemark", bbox[0] - gap, ylevel)

# Special case of holam haser (left) with rafe (right)
def AddHolamRafeGPOS(font):

    holam = font["afii57806"]
    rafe  = font["afii57841"]
    holam_width = - holam.left_side_bearing - holam.right_side_bearing
    rafe_width = - rafe.left_side_bearing - rafe.right_side_bearing
    gap   = utils.GetMarkToMarkGap(font, "patah.narrow", "tsere.narrow")
    center_to_center = gap + (holam_width + rafe_width) / 2

    for mark in InitHebrewGlyphData.GetVowelEquiv()["UpperToBase"]:
        font[mark].addAnchorPoint("CtxAnchors_Rafe", "mark", 0, 0)

    for glyph_class in InitHebrewGlyphData.GetGlyphEquiv():

        (holam_anchor_class, holam_basewidth) = utils.GetClassProperty(font, glyph_class, "DiaToBaseO")
        (rafe_anchor_class, rafe_basewidth) = utils.GetClassProperty(font, glyph_class, "UpperToBase")

        if holam_anchor_class is None:
            holam_anchor_class = 0
            holam_basewidth = font[glyph_class[0]].width

        if rafe_anchor_class is None:
            continue

        for glyph in glyph_class:

            # Fix for glyphs whose width was modified by dagesh
            holam_anchor = holam_anchor_class + font[glyph].width - holam_basewidth
            rafe_anchor = rafe_anchor_class + font[glyph].width - rafe_basewidth

            rafe_displacement = rafe_anchor - holam_anchor - center_to_center

            if rafe_displacement >= 0:
                continue

            font[glyph].addAnchorPoint("CtxAnchors_Rafe", "base", rafe_anchor - rafe_displacement, 0)

# Special case of sin/shin dot (left or right) with rafe
def AddShinDotRafeGPOS(font):

    shdot = font["afii57804"]
    sdot  = font["afii57803"]
    rafe  = font["afii57841"]
    sdot_width = - sdot.left_side_bearing - sdot.right_side_bearing
    rafe_width = - rafe.left_side_bearing - rafe.right_side_bearing
    gap   = utils.GetMarkToMarkGap(font, "afii57793", "afii57798") # hiriq-patah
    center_to_center = gap + (sdot_width + rafe_width) / 2

    for mark in InitHebrewGlyphData.GetVowelEquiv()["UpperToBase"]:
        font[mark].addAnchorPoint("CtxAnchors_Rafe", "mark", 0, 0)

    shindot_pos = (shdot.left_side_bearing - shdot.right_side_bearing) / 2
    sindot_pos = (sdot.left_side_bearing - sdot.right_side_bearing) / 2

    rafe_anchor = utils.GetClassProperty(font, ["afii57689"], "UpperToBase")[0]
    rafe_pos = (rafe.left_side_bearing - rafe.right_side_bearing) / 2 + rafe_anchor

    shin_rafe_displacement = shindot_pos - rafe_pos - center_to_center
    sin_rafe_displacement = rafe_pos - sindot_pos - center_to_center

    if (shin_rafe_displacement < 0):
        font["uniFB2A"].addAnchorPoint("CtxAnchors_Rafe", "base", rafe_anchor + shin_rafe_displacement, 0)
        font["uniFB2C"].addAnchorPoint("CtxAnchors_Rafe", "base", rafe_anchor + shin_rafe_displacement, 0)

    if (sin_rafe_displacement < 0):
        font["uniFB2B"].addAnchorPoint("CtxAnchors_Rafe", "base", rafe_anchor - sin_rafe_displacement, 0)
        font["uniFB2D"].addAnchorPoint("CtxAnchors_Rafe", "base", rafe_anchor - sin_rafe_displacement, 0)

# Special case of patah and hiriq after lamed (Yerushalam)
def AddYerushalamGPOS(font):

    fmem  = font["afii57677"]
    hiriq = font["afii57793"]

    # Align final mem and hiriq by right boundary
    # NOTE: final mem has positive bearing, but hiriq has negative bearing
    hiriq_anchor = -fmem.right_side_bearing + hiriq.right_side_bearing

    # Address slanted font
    height = fmem.boundingBox()[3] - hiriq.boundingBox()[3]
    hiriq_anchor += height * math.sin(math.radians(font.italicangle))

    font["afii57676"].addAnchorPoint("CtxAnchors_Yerushalam", "base", hiriq_anchor, 0)
    font["uniFB3C"].addAnchorPoint("CtxAnchors_Yerushalam", "base", hiriq_anchor, 0)

def AddHebrewContextualGPOS(unused, font):

    AddHebrewMarkToMarkGPOS(font)

    font.mergeFeature(script_dir + "/ContextualGPOS.fea")

    for comb, contents in InitHebrewGlyphData.GetMarkCombinations().items():
        for right_mark in contents[2]:

            right_width = - font[right_mark].left_side_bearing - font[right_mark].right_side_bearing
            width_list = []

            for left_mark in contents[1]:

                left_width = - font[left_mark].left_side_bearing - font[left_mark].right_side_bearing
                gap = utils.GetMarkToMarkGap(font, left_mark, right_mark)

                if gap is None:
                    print("No gap", left_mark, right_mark)
                    continue

                width_list.append(right_width + gap + left_width)

            if (len(width_list) == 0):
                continue

            max_width = max(width_list)
            min_width = min(width_list)
            width = (max_width + min_width) / 2
            mark_anchor = (right_width - width) / 2

            font[right_mark].addAnchorPoint(comb, "mark", mark_anchor, 0)

            for glyph_class in InitHebrewGlyphData.GetGlyphEquiv():

                (base_anchor, base_width) = utils.GetClassProperty(font, glyph_class, contents[0])

                if base_anchor is None:
                    continue

                for glyph in glyph_class:
                    # Fix for glyphs whose width was modified by dagesh
                    anchor_fix = font[glyph].width - base_width

                    font[glyph].addAnchorPoint(comb, "base", base_anchor + anchor_fix, 0)

    AddHolamRafeGPOS(font)
    AddShinDotRafeGPOS(font)
    AddYerushalamGPOS(font)
