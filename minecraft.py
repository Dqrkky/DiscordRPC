import requests
import time

def change_status(details :str=None, state :str=None):
    print(f'{details}\n{state}')

def get_level_from_xp(total_xp: int) -> tuple[int, float]:
    level = 0
    xp_for_level = 0
    while True:
        if level <= 16:
            xp_needed = 2 * level + 7
        elif level <= 31:
            xp_needed = 5 * level - 38
        else:
            xp_needed = 9 * level - 158
        if total_xp < xp_for_level + xp_needed:
            break
        xp_for_level += xp_needed
        level += 1
    progress = (total_xp - xp_for_level) / xp_needed
    return level, progress

def get_current_real_time():
    # Get current local time in HH:MM:SS format
    current_time = time.localtime()  # Get the current local time as a struct
    real_time = time.strftime(
        "%d/%m/%Y %H:%M", current_time
    )  # Format it as HH:MM:SS
    return real_time

# Build armor names safely
def extract_enchantments(components):
    """Extract enchantments from the components of an item."""
    enchantments = []
    if not components:
        return ""
    for comp in components:
        if "itemEnchantable" in comp:
            enchantments_data = comp["itemEnchantable"].get("enchantments", [])
            for enchant in enchantments_data:
                level = enchant.get("level", 0)
                enchantment_name = enchant["type"][
                    "id"
                ].capitalize()  # Capitalize the enchantment name
                enchantments.append(f"{enchantment_name[:4]} {level}")
    return ", ".join(enchantments) if enchantments else ""

def extract_durability(components):
    if not components:
        return None, None
    for comp in components:
        if "itemDurability" in comp:
            return comp["itemDurability"].get("damage"), comp[
                "itemDurability"
            ].get("maxDurability")
    return None, None

def format_armor_piece(slot, piece):
    """Format the armor piece with name, durability, and enchantments."""
    if not piece:
        return f"[{slot.title()}]: None"
    name = (
        piece.get("typeId", "unknown").split(":")[-1].replace("_", " ").title()
    )
    components = piece.get("getComponents", [])
    damage, max_durability = extract_durability(components)
    enchantments = extract_enchantments(components)
    if damage is None or max_durability is None:
        return f"[{slot.title()}]: {name} (No durability info)"
    durability_percent = 100 - int((damage / max_durability) * 100)
    enchantment_str = f" | [Ench]: {enchantments}" if enchantments else ""
    return f"[{slot.title()}]: {name} | [Dura]: {durability_percent}%{enchantment_str}"

def minecraft_stats(rss):
    try:
        req = rss.request(
            **{
                "method": "get",
                "url": "http://localhost:8000/worlds/Main/behavior_packs/Functions/scripts/index.php/player",
                "params": {"name": "Steeve1169"},
                "headers": {"User-Agent": "safadfgad"},
                "timeout": 30,
            }
        )
    except Exception as error:
        req = error
    if isinstance(req, requests.models.Response):
        data = req.json()
        if "error" in data:
            # Player not found, handle the error gracefully
            change_status(details="[Minecraft]", state=f"Error: {data['error']}")
            time.sleep(30)
            return
        dimension = data.get("coordinates", {}).get("dimension", {}).get("name", "")
        level, progress = get_level_from_xp(int(data.get("xp", "")))
        armor = data.get("armmor", {})
        armor_messages = [
            format_armor_piece("Head", armor.get("head", None)),
            format_armor_piece("Chest", armor.get("chest", None)),
            format_armor_piece("Legs", armor.get("legs", None)),
            format_armor_piece("Feet", armor.get("feet", None)),
            format_armor_piece("MainHand", armor.get("mainhand", None)),
            format_armor_piece("OffHand", armor.get("offhand", None)),
        ]
        for message in [
            f"[DateDime]: {get_current_real_time()}",
            f'[Name]: {data.get("name", "")}',
            f'[PlatformType]: {data.get("platformType", "")}',
            f"[Level]: {level} + {progress*100:.1f}% progress",
            f"[Dimension]: {dimension}",
            *armor_messages,
        ]:
            if message != None:  # noqa: E711
                change_status(details="[Minecraft]", state=message)
                time.sleep(10)