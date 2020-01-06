from constants import *

g_item_classes = {}
def register_item_class(name, item_class):
  if name in g_item_classes:
    raise Exception("register_item_class duplicate: %s" % name)

  g_item_classes[name] = item_class

def item_class(name):
  def reg(handler):
    register_item_class(name, handler)
    return handler
  return reg

class ItemPos(object):
  def __init__(self):
    self.type = ITEMPOS_VOID
    self.reset_props()

  def reset_props(self):
    self.map_x = None
    self.map_y = None
    self.inv_owner = None  # Mob
    self.inv_slot = None
    self.equip_owner = None  # Mob
    self.equip_slot = None
    self.holding_owner = None  # Mob

  def set_void(self):
    self.reset_props()
    self.type = ITEMPOS_VOID

  def set_map(self, x, y):
    self.reset_props()
    self.type = ITEMPOS_MAP
    self.map_x = x
    self.map_y = y

  def set_inventory(self, owner, slot):
    self.reset_props()
    self.type = ITEMPOS_INVENTORY
    self.inv_owner = owner
    self.inv_slot = slot

  def set_equipment(self, owner, slot):
    self.reset_props()
    self.type = ITEMPOS_EQUIPMENT
    self.equip_owner = owner
    self.equip_slot = slot

  def set_holding(self, owner):
    self.reset_props()
    self.type = ITEMPOS_HOLDING
    self.holding_owner = owner


class Item(object):
  def __init__(self):
    # Initial values are for a non-existing item.
    self.id = ITEM_NON_EXISTING_ID
    self.movable = False
    self.gfx_id = ""
    self.name = ""
    self.blocking = False  # True means it blocks the way.
    self.type = ""  # Optional type field.

    self.pos_x, self.pos_y = None, None  # Position if on map.
    self.pos = ItemPos()

  def use(self, player, world):
    pass

  def wakeup(self, data):
    for k, v in data.items():
      setattr(self, k, v)
    if not self.gfx_id:
      self.gfx_id = str(self.type)


