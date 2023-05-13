from math import tan, pi

import fontforge
import InitHebrewGlyphData

def SetGlyphCommentProperty(glyph, prop, value):

    try:
        value = int(value)
    except Exception:
        pass # Do nothing, retain existing value

    props = glyph.comment.split("\n")
    prop_idx = next((i for i, elem in enumerate(props) if elem.startswith("%" + prop + "=")), None)

    if prop_idx is None and value is None:
        pass
    elif prop_idx is None:
        props.append("%" + prop + "=" + str(value))
    elif value is None:
        # Remove the comment
        props.pop(prop_idx)
    else:
        props[prop_idx] = "%" + prop + "=" + str(value)

    props.sort()

    glyph.comment = "\n".join(props)

def GetGlyphCommentProperty(glyph, prop):

    props = glyph.comment.split("\n")
    prop_idx = next((i for i, elem in enumerate(props) if elem.startswith("%" + prop + "=")), None)

    if prop_idx is None:
        value = None
    else:
        value = props[prop_idx].split("=")[1]
        try:
            value = int(value)
        except ValueError:
            pass # Do nothing, retain existing value

    return value

def GetClassProperty(font, glyph_list, prop):

    good_glyphs = [g for g in glyph_list if (g in font and GetGlyphCommentProperty(font[g], prop) is not None)]

    if not good_glyphs:
        return (None, None)
    else:
        return (GetGlyphCommentProperty(font[good_glyphs[0]], prop), font[good_glyphs[0]].width)

def GetMarkToMarkGap(font, mark_from, mark_to):

    class_from = next((c for c, l in InitHebrewGlyphData.GetVowelRightEquiv().items() if mark_from in l), None)
    list_to = next((l for l in InitHebrewGlyphData.GetVowelLeftEquiv() if mark_to in l), None)

    if class_from is None or list_to is None:
        return None
    else:
        return GetClassProperty(font, list_to, class_from)[0]

def Unslant(contour, slanting_angle):
    unslanted = contour.dup()
    for pt in unslanted:
        pt.x += pt.y * tan(slanting_angle * pi / 180)

    return unslanted