import sys
sys.path.append('..')

from constants import *
from item import *

class ItemDoor(Item):
  def __init__(self, teleport_group=None):
    Item.__init__(self)
    self.movable = False
    self.gfx_id = "!"
    self.name = "Door"
    self.type = "door"

    self.teleport_group = teleport_group
    self.teleport_group_items = None

  def find_teleports(self, world):
    self.teleport_group_items = []

    for k, item in world.items.items():
      if item.type != "door":
        continue

      if item.teleport_group == self.teleport_group:
        self.teleport_group_items.append(item)

  def teleport(self, mob, world):
    if self.teleport_group_items is None:
      self.find_teleports(world)

    if len(self.teleport_group_items) == 1:
      if mob.type == MOB_TYPE_PLAYER:
        mob.show_text("Funny, this door doesn't seem to lead anywhere.")
        if self.pos_x == 410 and self.pos_y == 346:
          mob.show_text("I could have sworn there was a maze here!")
      return

    dst = None
    for item in self.teleport_group_items:
      diff_x = abs(item.pos_x - mob.pos_x)
      diff_y = abs(item.pos_y - mob.pos_y)
      if diff_x + diff_y == 1:
        continue
      dst = item

    if dst is None:
      return

    for d, x, y in [
        ( DIR_NORTH, 0, -1 ),
        ( DIR_SOUTH, 0,  1 ),
        ( DIR_WEST, -1, 0 ),
        ( DIR_EAST, 1, 0 ),
    ]:
      cx = dst.pos_x + x
      cy = dst.pos_y + y
      idx = cx + cy * 512
      candidate_tile = world.map.terrain[idx]
      if candidate_tile in BLOCKING_TILES:
        continue

      old_x, old_y = mob.pos_x, mob.pos_y
      world.map.move_mob(mob, cx, cy)
      if mob.type == "player":
        mob.direction = d
        mob.send_position()
        world.broadcast_mobs(cx, cy, ignore=mob)
      else:
        world.broadcast_mobs(cx, cy)
      world.broadcast_mobs(old_x, old_y)

class ItemCaveDoor(ItemDoor):
  def __init__(self, teleport_group=None):
    ItemDoor.__init__(self)
    self.name = "Cave Door"

  def wakeup(self, data):
    ItemDoor.wakeup(self, data)
    self.type = "door"  # Override to act as a teleport.


register_item_class("door", ItemDoor)
register_item_class("cave_door", ItemCaveDoor)

