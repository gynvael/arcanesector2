import sys
sys.path.append('..')

import os
from constants import *
from mob import *
from item import *
import misc_items
import time
import random

class FlagSeller(Mob):
  def __init__(self, world):
    Mob.__init__(self, world)

    self.gfx_id = "3d_mob_drow_m_green"
    self.name = "Flag Merchant"
    self.killable = False

  def on_heard_talking(self, event_source, text):
    if text is None:
      return

    if event_source.type != MOB_TYPE_PLAYER:
      return

    player = event_source
    text = text.lower()

    if "hello" in text:
      self.say_to(player, "Hello there! How can I be of service?")
      self.note_to(player, "Say 'buy flag' to buy the flag")
      return

    if "buy flag" in text:
      FLAG_COST = 100000
      if player.gold >= FLAG_COST:
        player.gold -= FLAG_COST
        self.say_to(player, "Why of course, happy to do business with you!")
        player.send_stats()

        try:
          with open("flags/flag_expensive.txt") as f:
            text = f.read().strip()
        except IOError:
          text = "ERROR: Contact CTF admin, this should not happen."
        note = self.world.register_item(
            misc_items.ItemNote(text, "An Expensive Flag", "sealed_letter"))
        player.add_to_inventory(note)
        player.send_inventory()
        player.send_ground()
      else:
        self.say_to(player, "I'm afraid you do not have enough money on you.")
        self.say_to(
            player, "You need %i gold pieces to afford the flag." % FLAG_COST)
      return

    self.say_to(player, "Excuse me?")
    self.note_to(player, "Start with saying 'hello'")


class Gambler(Mob):
  def __init__(self, world):
    Mob.__init__(self, world)

    self.gfx_id = "3d_mob_drow_m"
    self.name = "Gambler"
    self.killable = False
    self.gamblers = {}
    self.seed = bytearray(os.urandom(32))

  def on_heard_talking(self, event_source, text):
    if text is None:
      return

    if event_source.type != MOB_TYPE_PLAYER:
      return

    player = event_source
    text = text.lower().strip()

    if "hello" in text:
      self.say_to(player, "Hello. Do you feel lucky today traveler?")
      self.say_to(player, "If you beat my challenge, I'll give you a flag.")
      self.note_to(player, "Say 'gamble' to start the challenge (costs 10 gp)")
      return

    if "gamble" in text:
      if player.gold < 10:
        self.say_to(player, "Sorry to say it, but it seem you don't have anything to bet.")
        return
      player.gold -= 10
      player.send_stats()

      self.say_to(player, "Perfect! Get ready!")
      for _ in self.world.YIELDING_sleep(1.0):  # yield from
          yield _
      self.say_to(player, "I'm thinking of a number between 0 and 10000000000. Can you guess it?")
      self.gamblers[player.id] = self.gen_number(player)
      return

    try:
      v = int(text)
    except ValueError:
      self.say_to(player, "I'm sorry? Could you repeat?")
      self.note_to(player, "Start with saying 'hello'")
      return

    if player.id not in self.gamblers:
      self.say_to(player, "You have to tell me when to start.")
      self.note_to(player, "Say 'gamble' to start the challenge (costs 10 gp)")
      return

    good = self.gamblers[player.id]
    del self.gamblers[player.id]

    if v != good:
      self.say_to(player, "Ah, no. I was actually thinking of %i." % good)
      return

    self.say_to(player, "Well done! Here's your reward.")
    try:
      with open("flags/flag_gambler.txt") as f:
        text = f.read().strip()
    except IOError:
      text = "ERROR: Contact CTF admin, this should not happen."

    note = self.world.register_item(
        misc_items.ItemNote(text, "An Gambled Flag", "sealed_letter"))

    player.add_to_inventory(note)
    player.send_inventory()
    player.send_ground()

  def gen_number(self, player):
    n = 146410935049

    for v in self.seed[:16]:
      n = (n + v * 186577649851) % 257084507917

    n = (n ^ (int(time.time()) * 117865751629)) % 257084507917

    for v in self.seed[16:]:
      n = (n + v * 186577649851) % 257084507917

    n = (n + player.id * 117865751629) % 257084507917

    return n % 10000000000

class MasterSergeant(Mob):
  def __init__(self, world):
    Mob.__init__(self, world)

    self.gfx_id = "3d_mob_drow_f_ms"
    self.name = "Master Sergeant"
    self.killable = False
    self.quest_completed = set()

  def on_heard_talking(self, event_source, text):
    if text is None:
      return

    if event_source.type != MOB_TYPE_PLAYER:
      return

    player = event_source
    text = text.lower()

    if player.id in self.quest_completed:
      self.say_to(player, "Appreciate the amulets. We'll take it from here.")
      return

    if "hello" in text:
      self.say_to(player, "Well well. You look like someone who wants a flag.")
      for _ in self.world.YIELDING_sleep(3.0):  # yield from
          yield _
      self.say_to(player, "Good. Because there is something I need to finish my business here.")
      for _ in self.world.YIELDING_sleep(3.0):  # yield from
          yield _
      self.say_to(player, "Bring me 5 Blessed Amulets, and I will give you the flag.")
      self.note_to(player, "Say 'give amulets' once you have them in your inventory.")
      return

    if "give amulets" in text:
      amulets = []
      for item in player.inventory:
        if item == None or item == self.world.NON_EXISTING_ITEM or item.id == ITEM_NON_EXISTING_ID:
          continue
        if item.type == "blessed_amulet":
          amulets.append(item)

      if len(amulets) == 0:
        self.say_to(player, "Come back when you have the goods.")
        return

      if len(amulets) < 5:
        self.say_to(player, "Doesn't seem like you have enough. I need 5.")
        return

      for item in amulets:
        item.id = ITEM_NON_EXISTING_ID

      self.quest_completed.add(player.id)
      self.say_to(player, "Great doing business with you.")
      try:
        with open("flags/flag_master.txt") as f:
          text = f.read().strip()
      except IOError:
        text = "ERROR: Contact CTF admin, this should not happen."

      note = self.world.register_item(
          misc_items.ItemNote(text, "Master Sergeant's Flag", "sealed_letter"))

      player.add_to_inventory(note)
      player.send_inventory()
      player.send_ground()


      return

    self.say_to(player, "What?")
    self.note_to(player, "Start with saying 'hello'")
    return

class DrowParty(Mob):
  def __init__(self, world):
    Mob.__init__(self, world)

    self.gfx_id = random.choice([
        "3d_mob_drow_f_party",
        "3d_mob_drow_m_party"
    ])
    self.name = "Mage"
    self.killable = False

  def on_heard_talking(self, event_source, text):
    if text is None:
      return

    if event_source.type != MOB_TYPE_PLAYER:
      return

    player = event_source

    msg = random.choice([
        "You better talk with the Master Sergeant.",
        "Chat with Master Sergeant over there.",
        "Master Sergeant is there, talk with her.",
        "Looking for our leader? She's just there.",
        "You probably want to talk with Master Sergeant.",
        "What?",
        "I'm not the one you should be talking to."
    ])

    self.say_to(player, msg)

class IngotCollector(Mob):
  def __init__(self, world):
    Mob.__init__(self, world)

    self.gfx_id = "3d_mob_drow_f"
    self.name = "Collector"
    self.killable = False

  def on_heard_talking(self, event_source, text):
    if text is None:
      return

    if event_source.type != MOB_TYPE_PLAYER:
      return

    player = event_source
    text = text.lower()

    if "hello" in text:
      self.say_to(player, "Good day. I am Lledrith, a metal ingot collector.")
      self.say_to(player, "I will buy any ingot type I don't yet have off of you for 1000 gold pieces.")
      self.note_to(player, "Say 'sell ingot' to sell an ingot")
      return

    if "sell ingot" in text:
      self.say_to(player, "Excellent. Which ingot do you want to sell?")
      for _ in player.YIELDING_select():  # yield from
        if _ is False:
          self.say_to(player, "Another time then.")
          return
        yield _

      if player.select_result is None:
        self.say_to(player, "Another time then.")
        return

      target_type, target = player.select_result
      if target_type != "item":
        self.say_to(player, "What? Please don't jest with me.")
        return

      item, item_location, item_location_info = target

      if item.type != "ingot":
        self.say_to(player, "Certainly doesn't look like a metal ingot.")
        return

      unique = True
      for ingot_candidate in self.inventory:
        if ingot_candidate is None:
          continue
        if ingot_candidate is self.world.NON_EXISTING_ITEM:
          continue
        if ingot_candidate.id == ITEM_NON_EXISTING_ID:
          continue
        if ingot_candidate.type != "ingot":
          continue

        ingot = ingot_candidate

        if ingot.metal_type == item.metal_type:
          unique = False
          break

      if not unique:
        self.say_to(player, "I seem to have this metal ingot type already in my possession.")
        return

      self.world.reclaim_item(item)
      self.add_to_inventory(item)

      self.say_to(player, "Perfect! This will be a great addition to my collection.")
      self.say_to(player, "Here are your 1000 gold pieces.")
      player.gold += 1000

      player.send_inventory()
      player.send_ground()
      player.send_stats()
      return

    self.say_to(player, "... ?")
    self.note_to(player, "Start with saying 'hello'")


