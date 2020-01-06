#include <unordered_map>
#include <iterator>
#include <algorithm>
#include <list>
#include "items_helper.h"

using sprite_map_t = std::unordered_map<std::string, item_sprite_t>;
static sprite_map_t sprite_map;

static item_sprite_t normal_sprite(const std::string& img, int tile_x, int tile_y) {
  item_sprite_t item;
  item.img = img;
  item.w3d = 0.25f;
  item.h3d = 0.25f;
  item.is_sprite = true;
  item.x = tile_x * 16;
  item.y = tile_y * 16;
  item.w = 16;
  item.h = 16;
  return item;
}

static item_sprite_t world_item(
    const std::string& img, float w3d, float h3d, float x, float y, float z) {
  item_sprite_t item;
  item.img = img;
  item.w3d = w3d;
  item.h3d = h3d;
  item.has_position = true;
  item.x3d = x;
  item.y3d = y;
  item.z3d = z;
  return item;
}

void init_sprite_map() {
  // TODO: In an ideal world this would be loaded from a config file.
  sprite_map["__default"]      = normal_sprite("items_1", 11, 11);
  sprite_map["scroll"]         = normal_sprite("items_1", 9, 3);
  sprite_map["gold_key"]       = normal_sprite("items_1", 11, 3);
  sprite_map["teleport_ring"]  = normal_sprite("items_1", 1, 1);
  sprite_map["dagger"]         = normal_sprite("items_1", 0, 7);
  sprite_map["empty_flask"]    = normal_sprite("items_1", 11, 5);
  sprite_map["unknown_potion"] = normal_sprite("items_1", 9, 5);
  sprite_map["health_potion"]  = normal_sprite("items_1", 11, 4);
  sprite_map["mana_potion"]    = normal_sprite("items_1", 12, 4);
  sprite_map["herb_0"]         = normal_sprite("items_1", 0, 12);
  sprite_map["herb_1"]         = normal_sprite("items_1", 1, 12);
  sprite_map["herb_2"]         = normal_sprite("items_1", 2, 12);
  sprite_map["herb_3"]         = normal_sprite("items_1", 3, 12);
  sprite_map["herb_4"]         = normal_sprite("items_1", 4, 12);
  sprite_map["herb_5"]         = normal_sprite("items_1", 5, 12);
  sprite_map["herb_6"]         = normal_sprite("items_1", 6, 12);
  sprite_map["herb_7"]         = normal_sprite("items_1", 0, 13);
  sprite_map["herb_8"]         = normal_sprite("items_1", 1, 13);
  sprite_map["herb_9"]         = normal_sprite("items_1", 2, 13);
  sprite_map["herb_10"]        = normal_sprite("items_1", 3, 13);
  sprite_map["herb_11"]        = normal_sprite("items_1", 4, 13);
  sprite_map["herb_12"]        = normal_sprite("items_1", 5, 13);
  sprite_map["herb_13"]        = normal_sprite("items_1", 6, 13);
  sprite_map["pickaxe"]        = normal_sprite("items_2", 0, 12);
  sprite_map["ore_ironium"]    = normal_sprite("items_mining", 0, 1);
  sprite_map["ore_shadovium"]  = normal_sprite("items_mining", 1, 1);
  sprite_map["ore_titanium"]   = normal_sprite("items_mining", 2, 1);
  sprite_map["ore_copperium"]  = normal_sprite("items_mining", 3, 1);
  sprite_map["ore_cobaltium"]  = normal_sprite("items_mining", 4, 1);
  sprite_map["ore_aurium"]     = normal_sprite("items_mining", 5, 1);
  sprite_map["ore_amethystium"]= normal_sprite("items_mining", 6, 1);
  sprite_map["ore_royalium"]   = normal_sprite("items_mining", 7, 1);
  sprite_map["ore_dragonium"]  = normal_sprite("items_mining", 8, 1);
  sprite_map["ingot_ironium"]  = normal_sprite("items_mining", 0, 0);
  sprite_map["ingot_shadovium"]= normal_sprite("items_mining", 1, 0);
  sprite_map["ingot_titanium"] = normal_sprite("items_mining", 2, 0);
  sprite_map["ingot_copperium"]= normal_sprite("items_mining", 3, 0);
  sprite_map["ingot_cobaltium"]= normal_sprite("items_mining", 4, 0);
  sprite_map["ingot_aurium"]   = normal_sprite("items_mining", 5, 0);
  sprite_map["ingot_amethystium"]= normal_sprite("items_mining", 6, 0);
  sprite_map["ingot_royalium"] = normal_sprite("items_mining", 7, 0);
  sprite_map["ingot_dragonium"]= normal_sprite("items_mining", 8, 0);
  sprite_map["gold_coins_1"]   = normal_sprite("items_2", 0, 8);
  sprite_map["gold_coins_2"]   = normal_sprite("items_2", 1, 8);
  sprite_map["gold_coins_3"]   = normal_sprite("items_2", 2, 8);
  sprite_map["gold_coins_4"]   = normal_sprite("items_2", 3, 8);
  sprite_map["gold_coins_5"]   = normal_sprite("items_2", 4, 8);
  sprite_map["gold_coins_6"]   = normal_sprite("items_2", 5, 8);
  sprite_map["plain_note"]     = normal_sprite("items_1", 12, 10);
  sprite_map["opened_scroll"]  = normal_sprite("items_1", 9, 3);
  sprite_map["sealed_letter"]  = normal_sprite("items_2", 0, 7);
  sprite_map["opened_letter"]  = normal_sprite("items_2", 1, 7);
  sprite_map["closed_scroll"]  = normal_sprite("items_2", 1, 7);
  sprite_map["old_scroll_1"]   = normal_sprite("items_2", 13, 7);
  sprite_map["old_scroll_2"]   = normal_sprite("items_2", 14, 7);
  sprite_map["old_scroll_3"]   = normal_sprite("items_2", 15, 7);
  sprite_map["old_paper"]      = normal_sprite("items_2", 54, 7);
  sprite_map["empty_scroll"]   = normal_sprite("items_2", 52, 7);
  sprite_map["bound_scroll"]   = normal_sprite("items_2", 7, 7);
  sprite_map["quill"]          = normal_sprite("items_2", 26, 46);
  sprite_map["blessed_amulet"] = normal_sprite("items_2", 33, 5);
  sprite_map["sign"]           = world_item("sign", 1.0f, 1.8f, 0.0f, 0.0f, 0.0f);
  sprite_map["lamppost"]       = world_item("lamppost", 0.5f, 3.0f, 0.0f, 0.0f, 0.0f);
  sprite_map["book_stand"]     = world_item("book_stand", 1.0f, 1.8f, 0.0f, 0.0f, 0.0f);
}

std::list<std::string> item_sprite_map_keys() {
  std::list<std::string> keys;
  std::transform(
      sprite_map.begin(), sprite_map.end(),
      std::back_inserter(keys),
      [](const sprite_map_t::value_type &item) -> std::string {
        return item.first;
      }
  );

  return keys;
}

item_sprite_t item_to_sprite_info(const std::string& name) {
  auto ret = sprite_map.find(name);
  if (ret == sprite_map.end()) {
    return sprite_map["__default"];
  }

  return ret->second;
}
