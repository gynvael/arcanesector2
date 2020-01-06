import sys
sys.path.append('..')

from constants import *
from item import *
from spells import magic_spell

import random

@item_class("pickaxe")
class ItemPickaxe(Item):
  def __init__(self):
    Item.__init__(self)

    self.gfx_id = "pickaxe"
    self.name = "Pickaxe"
    self.type = "tool"
    self.movable = True

    self.last_used_locations = []

  def use(self, player, world):
    if player.busy:
      player.show_text("Seems you're doing something else already.")
      return

    n = self.gen_random(player) % 100000

    idx = player.pos_x + player.pos_y * 512
    if world.map.terrain[idx] != TILE_ROCKY_ROAD:
      player.show_text("You won't find any ore here.")
      return

    with player.busy_guard as move_count:
      player.show_text("You start digging...")

      for i in xrange(4):
        for _ in world.YIELDING_sleep(1.0):  # yield from
          yield _
        if player.move_count != move_count:
          player.show_text("You got distracted by something.")
          return

      # Probability ranges from 0 to 99999 (ranges are inclusive).
      metals = [
        ("ironium",     50000, 79999),
        ("shadovium",   80000, 89999),
        ("titanium",    90000, 94999),
        ("copperium",   95000, 97999),
        ("cobaltium",   98000, 98999),
        ("aurium",      99000, 99499),
        ("amethystium", 99500, 99959),
        ("royalium",    99960, 99998),
        ("dragonium",   99999, 99999),
      ]

      metal = None
      for candidate_metal, range_start, range_end in metals:
        if range_start <= n <= range_end:
          metal = candidate_metal
          break

      if metal is None:
        player.show_text("You didn't find any metal ore.")
        return

      ore = world.register_item(ItemOre(metal))
      player.add_to_inventory(ore)
      player.show_text("You dug up %s." % ore.name)

      player.send_inventory()
      player.send_ground()

  def gen_random(self, player):
    n = 0xf0e1d2c3

    for a, b, c in self.last_used_locations:
      k = a ^ (b << 8) ^ (c << 16)
      n = ((n << 3) ^ k) & 0xffffffff

    self.last_used_locations.append(
      (player.pos_x, player.pos_y, player.direction)
    )
    self.last_used_locations = self.last_used_locations[-10:]

    return n

@item_class("ore")
class ItemOre(Item):
  def __init__(self, metal):
    Item.__init__(self)

    names = {
      "ironium":     ("ore_ironium", "Ironium Ore"),
      "shadovium":   ("ore_shadovium", "Shadovium Ore"),
      "titanium":    ("ore_titanium", "Titanium Ore"),
      "copperium":   ("ore_copperium", "Copperium Ore"),
      "cobaltium":   ("ore_cobaltium", "Cobaltium Ore"),
      "aurium":      ("ore_aurium", "Aurium Ore"),
      "amethystium": ("ore_amethystium", "Amethystium Ore"),
      "royalium":    ("ore_royalium", "Royalium Ore"),
      "dragonium":   ("ore_dragonium", "Dragonium Ore"),
    }

    if metal not in names:
      raise Exception("Invalid Ore name \"%s\"" % metal)

    self.gfx_id, self.name = names[metal]
    self.type = "ore"
    self.metal_type = metal
    self.movable = True

@item_class("ingot")
class ItemIngot(Item):
  def __init__(self, metal):
    Item.__init__(self)

    names = {
      "ironium":     ("ingot_ironium", "Ironium Ingot"),
      "shadovium":   ("ingot_shadovium", "Shadovium Ingot"),
      "titanium":    ("ingot_titanium", "Titanium Ingot"),
      "copperium":   ("ingot_copperium", "Copperium Ingot"),
      "cobaltium":   ("ingot_cobaltium", "Cobaltium Ingot"),
      "aurium":      ("ingot_aurium", "Aurium Ingot"),
      "amethystium": ("ingot_amethystium", "Amethystium Ingot"),
      "royalium":    ("ingot_royalium", "Royalium Ingot"),
      "dragonium":   ("ingot_dragonium", "Dragonium Ingot"),
    }

    if metal not in names:
      raise Exception("Invalid Ingot name \"%s\"" % metal)

    self.gfx_id, self.name = names[metal]
    self.type = "ingot"
    self.metal_type = metal
    self.movable = True

@magic_spell("48")
def spell_smelt_ore(spell, player, world):
  player.show_text("Select ore for smelting.")

  for _ in player.YIELDING_select():  # yield from
    if _ is False:
      player.show_text("Spell canceled.")
      return
    yield _

  if player.select_result is None:
    player.show_text("Something's not right.")
    return

  target_type, target = player.select_result
  if target_type != "item":
    player.show_text("No metal ore selected.")
    return

  item, item_location, item_location_info = target

  if item.type != "ore":
    player.show_text("That's not metal ore.")
    return

  item.id = ITEM_NON_EXISTING_ID

  ingot = world.register_item(ItemIngot(item.metal_type))
  player.add_to_inventory(ingot)

  player.send_inventory()
  player.send_ground()




