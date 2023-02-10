import fontforge
import os.path
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

import CreatePrecomposedGlyphs
import Kern2Comments
import GuessMarkToMarkGaps
import AddHebrewGSUB
import AddHebrewGPOS
import Romanization

fontforge.registerMenuItem(CreatePrecomposedGlyphs.CreatePrecomposedGlyphs,None,None,"Font",None,"Create Precomposed Glyphs");
fontforge.registerMenuItem(Kern2Comments.Kern2Comments,None,None,"Font",None,"Convert Base-Mark Kernings to Position");
fontforge.registerMenuItem(GuessMarkToMarkGaps.GuessMarkToMarkGaps,None,None,"Font",None,"Guess Initial Mark To Mark Gaps");
fontforge.registerMenuItem(Romanization.BuildRomanization,None,None,"Font",None,"Build Romanization Characters");
fontforge.registerMenuItem(lambda a, b: False, lambda a, b: False,None,"Font",None, "-----------------------");
fontforge.registerMenuItem(AddHebrewGSUB.AddHebrewGSUB,None,None,"Font",None,"Add Hebrew GSUB");
fontforge.registerMenuItem(AddHebrewGPOS.AddHebrewGPOS,None,None,"Font",None,"Add Hebrew GPOS");

