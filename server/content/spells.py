import sys
import time
sys.path.append('..')

from constants import *
from item import *
import random

__all__ = ["spellcast", "magic_spell"]

g_spells = {}

def magic_spell(spell):
  def reg(handler):
    s = spell.decode("hex").ljust(8, '\0')
    g_spells[s] = handler
    return handler
  return reg

def get_spell_power(spell):
  count = 0
  for b in spell:
    if b != 0:
      count += 1
  return count

def spellcast_pay_mana(spell, player):
  power = get_spell_power(spell)

  required_mana = power * 5

  if required_mana > player.mana:
    player.show_text("Not enough mana.")
    return False

  player.mana -= required_mana
  player.send_stats()  # Might be redundant, but whatever.
  return True


def spellcast(spell, player, world, skip_mana=False):
  if not skip_mana:
    if not spellcast_pay_mana(spell, player):
      return

  handler = g_spells.get(str(spell))
  if handler is None:
    msg = "The spell failed miserably."
    if DEBUG_MODE:
      msg += " (%s)" % str(spell).encode("hex")
    player.show_text(msg)
    return

  return handler(str(spell), player, world)

@item_class("quill")
class ItemQuill(Item):
  def __init__(self):
    Item.__init__(self)
    self.movable = True
    self.type = "quill"
    self.gfx_id = "quill"
    self.name = "Scroll Quill"

  def use(self, player, world):
    player.show_text("Select the scroll you want to bind to:")

    for _ in player.YIELDING_select():  # yield from
      if _ is False:
        return
      yield _

    if player.select_result is None:
      player.show_text("Something's not right.")
      return

    target_type, target = player.select_result
    if target_type != "item":
      player.show_text("Something went wrong.")
      return

    item, item_location, item_location_info = target

    if not hasattr(item, 's'):
      player.show_text("That's not a spell scroll.")
      return

    player.hijack_spell = item
    player.show_text("Next spell you will cast will be instead bound to this scroll.")

@item_class("spell_scroll")
class ItemSpellScroll(Item):
  def __init__(self):
    Item.__init__(self)
    self.movable = True
    self.type = "spell_scroll"
    self.s = None
    self.reset_name_gfx()

  def reset_name_gfx(self):
    if self.s is None:
      self.gfx_id = "empty_scroll"
      self.name = "Unbound Scroll"
      return

    self.gfx_id = "bound_scroll"
    text = ["Scroll of "]
    for b in self.s:
      text.append("\xff")
      text.append(chr(b))
    self.name = ''.join(text)

  def use(self, player, world):
    if self.s is None:
      player.show_text("Nothing happens.")
      return

    spell = self.s
    self.s = None
    self.reset_name_gfx()
    player.send_inventory()
    player.send_ground()
    player.show_text("Magic leaves the scroll.")
    return spellcast(spell, player, world, skip_mana=True)

# -------------------------------------------------------------------
# Spells
# -------------------------------------------------------------------

@magic_spell("4a5a")
def spell_fire_arrow(spell, player, world):
  player.show_text("FIRE ARROW!!!!.... nothing happend")

@magic_spell("7071727374757677")
def spell_rebless(spell, player, world):
  player.show_text("Select a blessable item for random re-blessing:")

  for _ in player.YIELDING_select():  # yield from
    if _ is False:
      return
    yield _

  if player.select_result is None:
    player.show_text("Something's not right.")
    return

  target_type, target = player.select_result
  if target_type != "item":
    player.show_text("Something went wrong.")
    return

  item, item_location, item_location_info = target

  if not hasattr(item, "blessable") or not item.blessable:
    player.show_text("Wrong kind of item")
    return

  item_type = type(item)
  player.show_text("Summoning astral plane beings...")

  for _ in world.YIELDING_sleep(1.0):  # yield from
    yield _

  blessing_type = random.choice([
    "cosmic",
    "aetheric",
    "ghostic",
    "soulic",
    "magic",
    "voidic"
  ])

  player.show_text("A %s being answered!" % blessing_type)

  world.reclaim_item(item)
  item.id = ITEM_NON_EXISTING_ID
  item = world.register_item(item_type(blessing_type))
  player.add_to_inventory(item)
  player.send_inventory()
  player.send_ground()

@magic_spell("515151")
def spell_force_ram(spell, player, world):
  # Shove a mob away.
  player.show_text("Select who you want to ram:")

  for _ in player.YIELDING_select():  # yield from
    if _ is False:
      return
    yield _

  if player.select_result is None:
    player.show_text("Nevermind...")
    return

  target_type, target = player.select_result
  if target_type != "mob":
    player.show_text("You can only shove away mobs.")
    return

  if (player.pos_x != target.pos_x or
      player.pos_y != target.pos_y):
    player.show_text("The target is too far away.")
    return

  move_vector = DIR_TO_VECTOR[player.direction]
  pos_candidate = (
      target.pos_x + move_vector[0],
      target.pos_y + move_vector[1]
  )

  if (pos_candidate[0] < 0 or pos_candidate[0] >= 512 or
      pos_candidate[1] < 0 or pos_candidate[1] >= 768):
    player.show_text("Can't push the target of the edge of the world!")
    return

  idx_candidate = pos_candidate[0] + pos_candidate[1] * 512

  candidate_tile = world.map.terrain[idx_candidate]
  if candidate_tile in BLOCKING_TILES:
    player.show_text("Can't push the target.")
    return

  items = world.map.get_items(pos_candidate[0], pos_candidate[1])
  if items:
    for item in items:
      if item.blocking:
        player.show_text("Can't push the target.")
        return

      if item.type == "teleport":
        player.show_text("A block of force hits the target and pushes it away!")
        item.teleport(target, world)
        if target.type == MOB_TYPE_PLAYER:
          target.show_text("You've been shoved away by a wall of force")
        return

  world.map.move_mob(target, pos_candidate[0], pos_candidate[1])
  if target.type == MOB_TYPE_PLAYER:
    target.send_position()
    target.show_text("You've been shoved away by a wall of force")
  world.broadcast_mobs(target.pos_x, target.pos_x)
  world.broadcast_mobs(player.pos_x, player.pos_y)
  player.show_text("A block of force hits the target and pushes it away!")

@item_class("teleport_ring")
class ItemTeleportRing(Item):
  def __init__(self):
    Item.__init__(self)
    self.movable = True
    self.gfx_id = "teleport_ring"

    self.name = "Teleport Ring (Unbound)"
    self.type = "teleport_ring"
    self.teleport_set = False
    self.teleport_x = None
    self.teleport_y = None

  def use(self, player, world):
    if not self.teleport_set:
      player.show_text("Ring not bound to any location. Use proper binding spell.")
      return

    player.show_text("Teleporting in 3...")
    for _ in world.YIELDING_sleep(1.0):  # yield from
      yield _

    player.show_text("Teleporting in 2...")
    for _ in world.YIELDING_sleep(1.0):  # yield from
      yield _

    player.show_text("Teleporting in 1...")
    for _ in world.YIELDING_sleep(1.0):  # yield from
      yield _

    idx = self.teleport_x + self.teleport_y * 512
    candidate_tile = world.map.terrain[idx]
    if candidate_tile in BLOCKING_TILES:
      player.show_text("You detected flawed binding")
      self.name = "Teleport Ring (Flawed)"
      return

    world.broadcast_mobs(player.pos_x, player.pos_y, ignore=player)
    world.map.remove_mob(player)
    player.pos_x = self.teleport_x
    player.pos_y = self.teleport_y
    world.map.add_mob(player)
    player.send_position()
    world.broadcast_mobs(player.pos_x, player.pos_y, ignore=player)
    player.show_text("You feel dizzy, but it seems the ring worked.")

@magic_spell("76777879")
def spell_bind_teleport_ring(spell, player, world):
  player.show_text("Select teleport ring you want to bind to this location")

  for _ in player.YIELDING_select():  # yield from
    if _ is False:
      return
    yield _

  if player.select_result is None:
    player.show_text("Aborting teleport ring bind.")
    return

  target_type, target = player.select_result
  if target_type != "item":
    player.show_text("Aborting teleport ring bind.")
    return

  item, item_location, item_location_info = target

  if item.type != "teleport_ring":
    player.show_text("Not a teleport ring, aborting spell.")
    return

  player.show_text("Starting location binding ritual...")
  item.teleport_x = player.pos_x
  item.teleport_y = player.pos_y
  backup_move_count = player.move_count
  item.teleport_set = False
  item.name = "Teleport Ring (Unbound)"

  for _ in world.YIELDING_sleep(1.0):  # yield from
    yield _

  player.show_text("Verifying location of planets...")

  for _ in world.YIELDING_sleep(1.0):  # yield from
    yield _

  player.show_text("Measuring disturbance of force...")

  for _ in world.YIELDING_sleep(1.0):  # yield from
    yield _

  player.show_text("Calming local aether fields...")

  for _ in world.YIELDING_sleep(1.0):  # yield from
    yield _

  player.show_text("Probing nearby dimensions...")

  for _ in world.YIELDING_sleep(1.0):  # yield from
    yield _

  if player.move_count != backup_move_count:
    player.show_text("Ritual failed! Don't move next time.")
    return

  item.name = "Teleport Ring (%i, %i)" % (item.teleport_x, item.teleport_y)
  item.teleport_set = True
  player.show_text("Teleport ring bound to new location!")
  player.send_inventory()
  player.send_ground()

@magic_spell("7070707070")
def spell_ghostly_visions(spell, player, world):
  x, y, d = player.pos_x, player.pos_y, player.direction
  player.show_text("You leave your body behind...")
  player.block_interactions = True
  player.allow_clip = True
  player.visible = False
  player.send_effect("ghostly_visions")

  for _ in world.YIELDING_sleep(13.0):  # yield from
    yield _

  player.show_text("You feel your body is pulling you back!")

  for _ in world.YIELDING_sleep(2.0):  # yield from
    yield _

  world.broadcast_mobs(player.pos_x, player.pos_y, ignore=player)
  world.map.remove_mob(player)
  player.pos_x = x
  player.pos_y = y
  player.direction = d
  world.map.add_mob(player)
  player.send_position()
  world.broadcast_mobs(player.pos_x, player.pos_y, ignore=player)

  player.send_effect("")
  player.show_text("You're back in your body.")
  player.block_interactions = False
  player.allow_clip = False
  player.visible = True
  player.send_ground()



