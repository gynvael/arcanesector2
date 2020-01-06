import sys
sys.path.append('..')

from constants import *
from item import *

@item_class("note")
class ItemNote(Item):
  def __init__(self, text="", name="Note", gfx_id="plain_note"):
    Item.__init__(self)
    self.gfx_id = gfx_id
    self.name = name
    self.text = str(text)
    self.movable = True

  def use(self, player, world):
    player.show_text("The note says: %s" % str(self.text))

@item_class("window0")
class ItemWindow1(Item):
  def __init__(self):
    Item.__init__(self)
    self.gfx_id = "!"
    self.name = "Window 0"

@item_class("window1")
class ItemWindow1(Item):
  def __init__(self):
    Item.__init__(self)
    self.gfx_id = "!"
    self.name = "Window 1"

@item_class("blessed_amulet")
class ItemBlessedAmulet(Item):
  def __init__(self, bless_type="vanilla"):
    Item.__init__(self)
    self.movable = True
    self.gfx_id = "blessed_amulet"

    self.name = "Blessed Amulet (%s)" % bless_type
    self.type = "blessed_amulet"
    self.blessable = True

  def use(self, player, world):
    player.show_text("You feel like something is watching you...")

