import os
import Queue
import sys
import time
import types
import random

from packets import *
from ev_common import *
from content import spells

# Setting for hearing distance.
MAX_DIST_CLOSE = 6
MAX_DIST_NEARBY = 10
MAX_DIST_AWAY = 15

MAX_DIST_CLOSE_SQ = MAX_DIST_CLOSE * MAX_DIST_CLOSE
MAX_DIST_NEARBY_SQ = MAX_DIST_NEARBY * MAX_DIST_NEARBY
MAX_DIST_AWAY_SQ = MAX_DIST_AWAY * MAX_DIST_AWAY

g_debug = sys.modules["__main__"].g_debug

class PacketEvents(GetHandlersMixin):
  def __init__(self, world):
    self.world = world

  def handle_SAYS(self, packet, player):
    text = escape_text(packet.text)
    if len(text) > 256:
      text = text[:256]

    # Depending on the distance there will be 3 different variants of text.
    # Close: Text as is.
    # Nearby: Lowercased.
    # A little further away: Random letters will be replaced by dots.
    # Players even further than that will not be able to hear the message at
    # all.
    text_close = text
    text_nearby = text.lower()
    text_away = ''.join([ch if random.randint(0, 1) == 0 else '.' for ch in text])

    msg_close = "\x13%s says: \x17%s" % (player.name, text_close)
    msg_nearby = "\x13%s says: \x17%s" % (player.name, text_nearby)
    msg_away = "\x13%s says: \x17%s" % (player.name, text_away)

    x = player.pos_x
    y = player.pos_y

    mobs = self.world.map.get_mobs_near(x, y, MAX_DIST_AWAY, ignore=player)
    for m in mobs:
      dx = x - m.pos_x
      dy = y - m.pos_y
      dist_sq = dx * dx + dy * dy

      if m.type == MOB_TYPE_PLAYER:
        if dist_sq <= MAX_DIST_CLOSE_SQ:
          m.show_text(msg_close)
        elif dist_sq <= MAX_DIST_NEARBY_SQ:
          m.show_text(msg_nearby)
        else:
          m.show_text(msg_away)
        continue

      if m.type == MOB_TYPE_NPC:
        if not hasattr(m, "on_heard_talking"):
          # Don't send events like this to uninterested mobs.
          continue

        text = text_close if m.pos_x == x and m.pos_y == y else None

        self.world.post_event({
            "event": EV_SPECIAL,
            "type": "heard_talking",
            "mob": m,
            "event_source": player,
            "text": text
        })

  def handle_MOVE(self, p, player):
    if p.direction > 3:
      return False

    actual_direction = MOVE_TO_DIR_TRANSLATION[player.direction][p.direction]
    move_vector = DIR_TO_VECTOR[actual_direction]

    pos_candidate = (
        player.pos_x + move_vector[0],
        player.pos_y + move_vector[1]
    )

    if (pos_candidate[0] < 0 or pos_candidate[0] >= 512 or
        pos_candidate[1] < 0 or pos_candidate[1] >= 768):
      player.show_text("Can't go there.")
      return False

    items = self.world.map.get_items(pos_candidate[0], pos_candidate[1])
    if items:
      for item in items:
        if item.blocking and not player.allow_clip:
          player.show_text("Way is blocked.")
          return False
        if item.type == "door":
          return item.teleport(player, self.world)

    idx = pos_candidate[0] + pos_candidate[1] * 512

    candidate_tile = self.world.map.terrain[idx]
    if candidate_tile in BLOCKING_TILES:
      #if candidate_tile == TILE_WATER:
      #  player.show_text("Looks deep, cold and otherwise unpleasant.")
      #else:
      #  player.show_text("Looks pretty solid.")
      if not (player.allow_clip and candidate_tile != TILE_NOTHING):
        return False

    old_x, old_y = player.pos_x, player.pos_y
    self.world.map.move_mob(player, pos_candidate[0], pos_candidate[1])
    player.send_position()
    player.show_text("%i,%i,%i" % (player.pos_x, player.pos_y, player.direction))
    self.world.broadcast_mobs(old_x, old_y, ignore=player)
    self.world.broadcast_mobs(player.pos_x, player.pos_y, ignore=player)

    # TODO: let nearby mobs know that the player updated their position
    # (actually post an event per mob)

  def handle_DIRE(self, p, player):
    if p.direction > 3:
      return False

    player.direction = p.direction
    player.send_position()
    player.show_text("%i,%i,%i" % (player.pos_x, player.pos_y, player.direction))

  def handle_CAST(self, p, player):
    if player.busy_casting:
      player.show_text("You are already casting another spell!")
      return

    if player.hijack_spell is not None:
      if not spells.spellcast_pay_mana(p.spell, player):
        return
      scroll = player.hijack_spell
      scroll.s = p.spell
      scroll.reset_name_gfx()
      player.hijack_spell = None
      player.show_text("The spell was pulled onto the scroll.")
      player.send_inventory()
      player.send_ground()
      player.send_stats()
      return

    player.busy_casting = True
    potential_generator = spells.spellcast(p.spell, player, self.world)
    if type(potential_generator) is types.GeneratorType:
      def no_longer_casting():
        for _ in potential_generator:
          yield _
        player.busy_casting = False
      return no_longer_casting()
    player.busy_casting = False
    return potential_generator

  def handle_HOLD(self, p, player):
    item_id = p.item_id
    if item_id == ITEM_NON_EXISTING_ID:  # What.
      if g_debug:
        print "Player tried to hold non-existing item"
      return False

    item_place = player.can_reach_item(item_id)
    if item_place is False:
      player.show_text("Out of reach.")
      return

    item = item_place[0]

    if not item.movable:
      player.show_text("Unable to take this item.")
      return

    # TODO: Perhaps use reclaim here for simplicity.
    if item_place[1] == "ground":
      self.world.map.remove_item(item)
      player.send_ground()
      self.world.broadcast_ground(player.pos_x, player.pos_y, ignore=player)
    elif item_place[1] == "inventory":
      player.inventory[item_place[2]] = self.world.NON_EXISTING_ITEM
      player.send_inventory()
    else:
      player.equipment[item_place[2]] = self.world.NON_EXISTING_ITEM
      player.send_inventory()

    player.hold_item(item)

  def handle_DROP(self, p, player):
    if player.holding.id == ITEM_NON_EXISTING_ID:
      return

    new_holding = self.world.NON_EXISTING_ITEM
    item = player.holding

    if 0 <= p.dst < 8:  # Inventory.
      idx = p.dst
      new_holding = player.inventory[idx]  # Might be empty.
      player.inventory[idx] = item
      item.pos.set_inventory(player, idx)
      player.send_inventory()
    elif 8 <= p.dst < 10:  # Equipment.
      idx = p.dst - 8
      new_holding = player.equipment[idx]  # Might be empty.
      player.equipment[idx] = item
      item.pos.set_equipment(player, idx)
      player.send_inventory()
    else:
      # Ground.
      player.holding.pos_x = player.pos_x
      player.holding.pos_y = player.pos_y
      self.world.map.add_item(item)
      player.send_ground()
      self.world.broadcast_ground(player.pos_x, player.pos_y, ignore=player)

    player.hold_item(new_holding)

  def handle_USEI(self, p, player):
    if player.block_interactions:
      player.show_text("Can't use items right now.")
      return

    item_id = p.item_id
    if item_id == ITEM_NON_EXISTING_ID:  # What.
      if g_debug:
        print "Player tried to use non-existing item"
      return False

    item_place = player.can_reach_item(item_id)
    if item_place is False:
      player.show_text("Out of reach.")
      return

    item = item_place[0]
    return item.use(player, self.world)

  def handle_THIS(self, p, player):
    # Ignore.
    return


