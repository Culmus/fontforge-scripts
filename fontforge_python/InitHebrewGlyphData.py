# Consonants equivalence list
def GetGlyphEquiv():

    return [ ["afii57664", "uniFB30"], # Aleph
             ["afii57665", "uniFB31"], # Bet
             ["afii57666", "uniFB32"], # Gimel
             ["afii57667", "uniFB33"], # Dalet
             ["afii57668", "uniFB34"], # He
             ["afii57669", "uniFB35"], # Vav
             ["afii57670", "uniFB36"], # Zayin
             ["afii57671", "uniFB37"], # Het
             ["afii57672", "uniFB38"], # Tet
             ["afii57673", "uniFB39"], # Yod
             ["afii57674"],            # Final Kaf
             ["afii57675", "uniFB3B"], # Kaf
             ["afii57676", "uniFB3C"], # Lamed
             ["afii57677"],            # Final Mem
             ["afii57678", "uniFB3E"], # Mem
             ["afii57679"],            # Final Nun
             ["afii57680", "uniFB40"], # Nun
             ["afii57681", "uniFB41"], # Samech
             ["afii57682", "uniFB42"], # Ayin
             ["uniFB20",   "uniE805"], # Ayin flat
             ["afii57683"],            # Final Fe
             ["afii57684", "uniFB44"], # Pe
             ["afii57685"],            # Final Tsadi
             ["afii57686", "uniFB46"], # Tsadi
             ["afii57687", "uniFB47"], # Quf
             ["afii57688", "uniFB48"], # Resh
             ["afii57689", "uniFB49", "uniFB2A", "uniFB2B", "uniFB2C", "uniFB2D"], # Shin
             ["afii57690", "uniFB4A"], # Tav
             ["uniFB3A"],              # Final Kaf dagesh
             ["uni25CC"]               # Dotted circle
           ]

# Vowels equivalence list
def GetVowelEquiv():

    return { # Single width diacritics
             "DiaToBase1" : ["afii57799", "afii57793", "afii57839", "meteg.right"],
             # Double width diacritics
             "DiaToBase2" : ["afii57794", "afii57795", "afii57798", "afii57797", "uni05C7"],
             # Triple width diacritics
             "DiaToBase3" : ["afii57801", "afii57800", "afii57802"],
             # Quadruple width diacritics (joined hataf-meteg)
             "DiaToBase4" : ["uniE806", "uniE807", "uniE808"],
             # Qubuts diacritic
             "DiaToBaseU" : ["afii57796"],
             # Holam diacritic
             "DiaToBaseO" : ["afii57806"],
             # Dagesh
             "DiaToBaseD" : ["afii57807"],
             # Rafe
             "RafeToBase" : ["afii57841", "uniFB1E"]
           }

# Vowels left shape equivalence list
def GetVowelLeftEquiv():

    return [ # Dot shape at the left side (like tsere)
             ["afii57793", "afii57794", "afii57795", "afii57801"],
             # Two dots shape at the left side (like shwa) - may differ from tsere
             # in slanted fonts
             ["afii57799"],
             # Bar shape at the left side (like patah)
             ["afii57798", "afii57797", "uni05C7", "afii57800", "afii57802"],
             # Column shape at the left side (like meteg)
             ["afii57839", "meteg.right"],
             # Dot shape at the left side - narrow glyph
             ["uniE806", "tsere.narrow", "segol.narrow", "hatafsegol.narrow", "afii57796"],
             # Bar shape at the left side - narrow glyph
             ["uniE807", "patah.narrow", "hatafpatah.narrow",
              "uniE808", "qamats.narrow", "hatafqamats.narrow"]
           ]

# Vowels right shape equivalence list
def GetVowelRightEquiv():

    return { # Dot shape at the right side (like tsere)
             "DotToBaseMark" : ["afii57793", "afii57794", "afii57795"],
             # 2 dots shape at the right side (like shwa)
             "2DotsToBaseMark" : ["afii57799", "afii57801", "afii57800", "afii57802"],
             # Bar shape at the right side (like patah)
             "BarToBaseMark" : ["afii57798", "afii57797", "uni05C7"],
             # Column shape at the right side (like meteg)
             "ColumnToBaseMark" : ["afii57839", "meteg.right"],
             # Dot shape at the right side - narrow glyph
             "DotToBaseNarrowMark" : ["tsere.narrow", "segol.narrow"],
             # 2 dots shape at the right side - narrow glyph
             "2DotsToBaseNarrowMark" : ["uniE806", "uniE807", "uniE808", "afii57796",
                                      "hatafsegol.narrow", "hatafpatah.narrow",
                                      "hatafqamats.narrow"],
              # Bar shape at the right side - narrow glyph
             "BarToBaseNarrowMark" : ["patah.narrow", "qamats.narrow"]
           }

def GetMarkCombinations():

    # Dictionary of entries as follows:
    # { Anchor_name : [Vowel_equivalence_class, list_of_left_marks, list_of_right_marks] }
    return { # Meteg (left) with 1-wide vowel (right)
             "CtxAnchors_M_D1" : ["DiaToBase2", ["afii57839"], GetVowelEquiv()["DiaToBase1"]],
             # Meteg (left) with 2-wide vowel (right)
             "CtxAnchors_M_D2" : ["DiaToBase3", ["afii57839"], GetVowelEquiv()["DiaToBase2"]],
             # Meteg (left) with 2-wide narrow vowel (right)
             "CtxAnchors_M_D2Narrow" : ["DiaToBase3", ["afii57839"],
                 ["tsere.narrow", "segol.narrow", "patah.narrow", "qamats.narrow"]],
             # Meteg (left) with 3-wide narrow vowel (right)
             "CtxAnchors_M_D3Narrow" : ["DiaToBase4", ["afii57839"],
                 ["hatafsegol.narrow", "hatafpatah.narrow", "hatafqamats.narrow"] + GetVowelEquiv()["DiaToBaseU"]],
             # 1-wide vowel (left) with meteg (right)
             "CtxAnchors_D1_M" : ["DiaToBase2", GetVowelEquiv()["DiaToBase1"], ["meteg.right"]],
             # 2-wide vowel (left) with meteg (right)
             "CtxAnchors_D2_M" : ["DiaToBase3", GetVowelEquiv()["DiaToBase2"], ["meteg.right"]],
             # 2-wide narrow vowel (left) with meteg (right)
             "CtxAnchors_D2Narrow_M" : ["DiaToBase3",
                 ["tsere.narrow", "segol.narrow", "patah.narrow", "qamats.narrow"], ["meteg.right"]],
             # 3-wide narrow vowel (left) with meteg (right)
             "CtxAnchors_D3Narrow_M" : ["DiaToBase4",
                 ["hatafsegol.narrow", "hatafpatah.narrow", "hatafqamats.narrow"] + GetVowelEquiv()["DiaToBaseU"],
                 ["meteg.right"]]
           }

# Mark side shapes [shape from left, shape from right]
def GetMarkShapes():

    return { "afii57799" : ["Dot", "Dot"], # Shwa
             "afii57793" : ["Dot", "Dot"], # Hiriq
             "afii57839" : ["Col", "Col"], # Meteg
             "afii57794" : ["Dot", "Dot"], # Tsere
             "afii57795" : ["Dot", "Dot"], # Segol
             "afii57798" : ["Bar", "Bar"], # Patah
             "afii57797" : ["Bar", "Bar"], # Qamats
             "afii57801" : ["Dot", "Dot"], # Hataf-Segol
             "afii57800" : ["Bar", "Dot"], # Hataf-Patah
             "afii57802" : ["Bar", "Dot"], # Hataf-Qamats
           }

# right side kerning equivalence list
def GetRightKernEquiv():
    return [ ["afii57664", "uniFB21", "uniFB2E", "uniFB2F", "uniFB30"], # Aleph
             ["afii57665", "uniFB31", "uniFB4C"], # Beth
             ["afii57666", "uniFB32"],            # Gimel
             ["afii57667", "uniFB22", "uniFB33"], # Dalet
             ["afii57668", "uniFB23", "uniFB34"], # He
             ["afii57669", "afii57716", "uniE801", "uniFB35", "uniFB4B"], # Vav
             ["afii57670", "uniFB36"],            # Zayin
             ["afii57671", "uniFB37"],            # Het
             ["afii57672", "uniFB38"],            # Tet
             ["afii57673", "afii57717", "afii57718", "uniE804", "uniFB1D", "uniFB1F", "uniFB39"], # Yod
             ["afii57674", "uniE802", "uniE803", "uniFB3A"], # Final Kaf
             ["afii57675", "uniFB24", "uniFB3B", "uniFB4D"], # Kaf
             ["afii57676", "uniFB25", "uniFB3C"], # Lamed
             ["afii57677", "uniFB26", "uniFB3D"], # Final Mem
             ["afii57678", "uniFB3E"],            # Mem
             ["afii57679", "uniFB3F"],            # Final Nun
             ["afii57680", "uniFB40"],            # Nun
             ["afii57681", "uniFB41"],            # Samech
             ["afii57682", "uniFB42"],            # Ayin
             ["uniFB20"],                         # Ayin flat
             ["afii57683", "uniFB43"],            # Final Fe
             ["afii57684", "uniFB44", "uniFB4E"], # Pe
             ["afii57685", "uniFB45"],            # Final Tsadi
             ["afii57686", "uniFB46"],            # Tsadi
             ["afii57687", "uniFB47"],            # Quf
             ["afii57688", "uniFB48"],            # Resh
             ["afii57689", "uniFB49", "uniFB2A", "uniFB2B", "uniFB2C", "uniFB2D"],    # Shin
             ["afii57690", "uniFB28", "uniFB4A"], # Tav
             ["quotesingle", "quotedbl", "uni05F3", "uni05F4", "quoteright", "quotedblright"], # quote
             ["period", "comma", "ellipsis"],
             ["colon", "semicolon", "afii57658"], # colon
           ]

# left side kerning equivalence list
def GetLeftKernEquiv():

    rlist = GetRightKernEquiv()

    zayin_idx = next((i for i,elem in enumerate(rlist) if elem[0] == "afii57670"))
    rlist[zayin_idx] = ["afii57670"]

    period_idx = next((i for i,elem in enumerate(rlist) if elem[0] == "period"))
    del rlist[period_idx]

    colon_idx = next((i for i,elem in enumerate(rlist) if elem[0] == "colon"))
    del rlist[colon_idx]

    return rlist
