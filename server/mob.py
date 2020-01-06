from constants import *

g_mob_classes = {}
def register_mob_class(name, mob_class):
  if name in g_mob_classes:
    raise Exception("register_mob_class duplicate: %s" % name)

  g_mob_classes[name] = mob_class

class Mob(object):
  def __init__(self, world):
    # Initial values are for a non-existing mob.
    self.world = world
    self.id = MOB_NON_EXISTING_ID  # Must be set when adding to the world.
    self.gfx_id = ""
    self.name = "Unknown"
    self.type = MOB_TYPE_NPC
    self.hp = 100
    self.hp_max = 100
    self.mana = 100
    self.mana_max = 100
    self.visible = True
    self.inventory = [world.NON_EXISTING_ITEM] * 8
    self.move_count = 0
    self.killable = True

    self.pos_x, self.pos_y = None, None  # Position if on map.

  """
  A mob class might want to register the following methods for event handling.

  def on_heard_talking(self, event_source, text):
    # event_source is a mob (usually a player)
    # text will be None if event_source is far away
    # it will be a string if event_source is at the exact same position as self
    pass

  """

  def update(self, player, world):
    # Do something?
    # TODO what is this function?
    pass

  def say_to(self, player, text):
    if player.type != MOB_TYPE_PLAYER:
      return
    msg = "\x13%s says: \x17%s" % (self.name, text)
    player.show_text(msg)

  def note_to(self, player, text):
    if player.type != MOB_TYPE_PLAYER:
      return
    player.show_text(text)

  def add_to_inventory(self, item):
    if (item is None or
        item is self.world.NON_EXISTING_ITEM or
        item.id == ITEM_NON_EXISTING_ID):
      return

    free_slot = None
    for i, inv_item in enumerate(self.inventory):
      if (inv_item is None or
          inv_item is self.world.NON_EXISTING_ITEM or
          inv_item.id == ITEM_NON_EXISTING_ID):
        free_slot = i
        break

    if free_slot is not None:
      self.inventory[free_slot] = item
      item.pos.set_inventory(self, free_slot)
      return

    if self.pos_x is None or self.pos_y is None:
      msg = ("error: item '%s' cannot be dropped under mob '%s', since the mob "
             "doesn't have x,y position set")
      print msg % (item.name, mob.name)
      return

    self.world.drop_item(item, self.pos_x, self.pos_y)
    if self.type == MOB_TYPE_PLAYER:
      self.show_text("Item dropped on the ground as inventory is full.")

  def remove_from_inventory(self, item):
    if (item is None or
        item is self.world.NON_EXISTING_ITEM or
        item.id == ITEM_NON_EXISTING_ID):
      return item

    for i, inv_item in enumerate(self.inventory):
      if item is inv_item:
        self.inventory[i] = self.world.NON_EXISTING_ITEM
        return item

    return item

  def wakeup(self, data):
    for k, v in data.mobs():
      setattr(self, k, v)
    if not self.gfx_id:
      self.gfx_id = str(self.type)

register_mob_class("mob", Mob)
