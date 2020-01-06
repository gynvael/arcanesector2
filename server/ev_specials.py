import os
import Queue
import sys
import time
import types
from random import randint

from packets import *
from world import *
from ev_common import *
from content import *

class SpecialEvents(GetHandlersMixin):
  def __init__(self, world):
    self.world = world

  def handle_basic_info_request(self, ev, player):
    # Send basic info to the player (usually after the client just connected, or
    # teleported somewhere).
    world = self.world

    player.send_stats(full=True)
    player.send_inventory()
    player.send_position()
    if player.holding.id != ITEM_NON_EXISTING_ID:
      world.post_packet(
          player.id,
          PacketSC_HLDI(player.holding)
      )

    msg = '\n'.join([
        "Welcome %s to \x12" "Arcane Sector II" "\x0f!" % player.name,
    ])

    player.show_text(msg)

  def spawn_item(self, ev, player, spawn):
    world = self.world

    if world.map.get_items(spawn["pos_x"], spawn["pos_y"]):
      # Something already there, ignore.
      return False

    # Spawn.
    class_to_factory = {
      "herb": lambda:herbs.ItemHerb(random.randint(0, 13)),
      "flask": flasks.ItemFlask,
      "teleport_ring": spells.ItemTeleportRing,
      "pickaxe": mining.ItemPickaxe,
      "spell_scroll": spells.ItemSpellScroll,
      "quill": spells.ItemQuill,
    }
    item_class = spawn["item_class"]
    if item_class not in class_to_factory:
      print "error: failed to find factory for item class '%s'" % item_class
      return False

    item_factory = class_to_factory[item_class]
    item = item_factory()

    if item:
      item.pos_x = spawn["pos_x"]
      item.pos_y = spawn["pos_y"]
      world.register_item(item)
      world.map.add_item(item)
      return True

    return False

  def spawn_mob(self, ev, player, spawn):
    world = self.world

    # Check if this specific mob is still alive (spawn points IDs are used as
    # mob IDs, so this can be done easily).
    if world.is_mob_alive_by_id(MOB_ID_OFFSET + spawn["id"]):
      return False  # Still alive.

    class_to_factory = {
        "npc_flag_expensive": lambda world: npc.FlagSeller(world),
        "npc_ingot_collector": lambda world: npc.IngotCollector(world),
        "npc_gambler": lambda world: npc.Gambler(world),
        "npc_drow_party": lambda world: npc.DrowParty(world),
        "npc_master_sergeant": lambda world: npc.MasterSergeant(world),
    }

    mob_class = spawn["mob_class"]
    if mob_class not in class_to_factory:
      print "error: failed to find factory for mob class '%s'" % mob_class
      return False

    mob_factory = class_to_factory[mob_class]
    mob = mob_factory(world)
    mob.id = MOB_ID_OFFSET + spawn["id"]
    mob.pos_x = spawn["pos_x"]
    mob.pos_y = spawn["pos_y"]

    world.register_mob(mob)
    world.map.add_mob(mob)

    return False

  def handle_spawners(self, ev, player):
    world = self.world

    while True:
      now = time.time()

      changes = False
      for spawn in world.map.spawners:
        if 'last' in spawn:
          when = spawn["last"] + spawn["cooldown"]
          if now < when:
            continue

        res = False
        if spawn["type"] == "spawn_item":
          res = self.spawn_item(ev, player, spawn)
        elif spawn["type"] == "spawn_mob":
          res = self.spawn_mob(ev, player, spawn)

        if res:
          spawn["last"] = now
          changes = True

      if changes:
        # TODO: push mob/item state to players
        pass

      for _ in world.YIELDING_sleep(30.0):  # yield from
        yield _

  def handle_heard_talking(self, ev, _):
    world = self.world
    mob = ev["mob"]

    if not hasattr(mob, "on_heard_talking"):
      # Mob isn't really interested.
      return

    return mob.on_heard_talking(ev["event_source"], ev["text"])

  def handle_item_guard(self, ev, _):
    # Periodically run checker to verify items are only in one location at a
    # time.
    world = self.world

    timeout = 10.0 if DEBUG_MODE else 600.0  # Seconds.

    while True:
      guard_report = ["Item Guard Report:"]

      # Check all items lying on the ground.
      for pos, items in world.map.item_map.items():
        for item in items:
          if item is None:
            continue
          if item is world.NON_EXISTING_ITEM:
            continue
          if item.id == ITEM_NON_EXISTING_ID:
            continue

          if item.pos.type != ITEMPOS_MAP:
            guard_report.append("item_map: type is not ITEMPOS_MAP: [%x: %s %s] at %x,%x" % (
                item.id, item.type, item.name,
                pos[0], pos[1]
            ))
            continue

          if item.pos.map_x != pos[0] or item.pos.map_y != pos[1]:
            guard_report.append("item_map: position mismatch: [%x: %s %s] at %x,%x has pos %x,%x" % (
                item.id, item.type, item.name,
                pos[0], pos[1],
                str(item.pos.map_x), str(item.pos.map_y)
            ))
            continue

      # Check all mob inventories, equipment and holding.
      for mob in world.mobs.values():
        if mob is None:
          continue
        if not world.is_mob_alive(mob):
          continue

        # Inventory
        for slot, item in enumerate(mob.inventory):
          if item is None:
            continue
          if item is world.NON_EXISTING_ITEM:
            continue
          if item.id == ITEM_NON_EXISTING_ID:
            continue

          if item.pos.type != ITEMPOS_INVENTORY:
            guard_report.append("item_inv: type is not ITEMPOS_INVENTORY: [%x: %s %s] owner [%x: %s %s] slot %i" % (
                item.id, item.type, item.name,
                mob.id, mob.type, mob.name,
                slot
            ))
            continue

          if item.pos.inv_slot != slot:
            guard_report.append("item_inv: slot mismatch: [%x: %s %s] owner [%x: %s %s] slot %i vs actual %i" % (
                item.id, item.type, item.name,
                mob.id, mob.type, mob.name,
                item.pos.inv_slot, slot
            ))
            continue

          if item.pos.inv_owner is not mob:
            guard_report.append("item_inv: owner mismatch [%x: %s %s] owner [%x: %s %s] slot %i vs actual owner [%x: %s %s]" % (
                item.id, item.type, item.name,
                item.pos.inv_owner.id, item.pos.inv_owner.type, item.pos.inv_owner.name,
                slot,
                mob.id, mob.type, mob.name,
            ))
            continue

        if mob.type == MOB_TYPE_PLAYER:
          # Equipment
          for slot, item in enumerate(mob.equipment):
            if item is None:
              continue
            if item is world.NON_EXISTING_ITEM:
              continue
            if item.id == ITEM_NON_EXISTING_ID:
              continue

            if item.pos.type != ITEMPOS_EQUIPMENT:
              guard_report.append("item_equip: type is not ITEMPOS_EQUIPMENT: [%x: %s %s] owner [%x: %s %s] slot %i" % (
                  item.id, item.type, item.name,
                  mob.id, mob.type, mob.name,
                  slot
              ))
              continue

            if item.pos.equip_slot != slot:
              guard_report.append("item_equip: slot mismatch: [%x: %s %s] owner [%x: %s %s] slot %i vs actual %i" % (
                  item.id, item.type, item.name,
                  mob.id, mob.type, mob.name,
                  item.pos.equip_slot, slot
              ))
              continue

            if item.pos.equip_owner is not mob:
              guard_report.append("item_equip: owner mismatch [%x: %s %s] owner [%x: %s %s] slot %i vs actual owner [%x: %s %s]" % (
                  item.id, item.type, item.name,
                  item.pos.equip_owner.id, item.pos.equip_owner.type, item.pos.equip_owner.name,
                  slot,
                  mob.id, mob.type, mob.name,
              ))
              continue

          # Holding
          item = mob.holding
          if item is None:
            continue
          if item is world.NON_EXISTING_ITEM:
            continue
          if item.id == ITEM_NON_EXISTING_ID:
            continue

          if item.pos.type != ITEMPOS_HOLDING:
            guard_report.append("item_hold: type is not ITEMPOS_HOLDING: [%x: %s %s] owner [%x: %s %s]" % (
                item.id, item.type, item.name,
                mob.id, mob.type, mob.name,
            ))
            continue

          if item.pos.holding_owner is not mob:
            guard_report.append("item_hold: owner mismatch [%x: %s %s] owner [%x: %s %s] vs actual owner [%x: %s %s]" % (
                item.id, item.type, item.name,
                item.pos.holding_owner.id, item.pos.holding_owner.type, item.pos.holding_owner.name,
                mob.id, mob.type, mob.name,
            ))
            continue

          continue
        continue

      if len(guard_report) > 1:
        print '\n  '.join(guard_report)

      for _ in world.YIELDING_sleep(timeout):  # yield from
        yield _



