from data_handler import DataHandler
from itertools import combinations, chain
from math import comb
import requests_cache
import re
import json
import hashlib

RELEVANT_MOD_STATS = ["Fire rate", "Multishot", "Status Chance", "Reload Speed", "Magazine Capacity"]
RELEVANT_WEAPON_STATS = ["fireRate", "multishot", "status_chance", "reloadTime", "magazineSize"]
RELEVANT_CONDITIONS = ["On Reload", "On Ability Cast"]
VARIANTS_TO_STRIP = ["GALVANIZED", "AMALGAM", "FLAWED"]
WEAPON_ATTACK = 0
WEAPON_MOD_SLOTS = 8
WEAPON_EXILUS_SLOTS = 1
CACHE_LIFESPAN = 60*60*24*1  # 1 days


class WeaponSimulator:
    weapon_name = None
    max_burst_seconds = None
    minimum_simulated_mods = None
    progress_display_mod = None
    locked_mod_names = None
    raw_mod_data = None

    def __init__(
            self, 
            weapon_name, 
            max_burst_seconds = 12,
            minimum_simulated_mods = 8,
            progress_display_mod = 1,
            locked_mod_names = []

    ):
        self.weapon_name = weapon_name
        self.max_burst_seconds = max_burst_seconds
        self.minimum_simulated_mods = minimum_simulated_mods
        self.progress_display_mod = progress_display_mod
        self.locked_mod_names = {name.lower() for name in locked_mod_names} 

        
    def run(self):
        # Collect data
        self.setup_cache()
        raw_mod_data = DataHandler.get_mods_data()
        raw_weapon_data = DataHandler.get_weapon_data()

        # Run simulation
        weapon = self.get_weapon(raw_weapon_data, self.weapon_name)
        mod_data, mod_data_exilus = self.get_relevant_mods(raw_mod_data, weapon)
        sim_results = self.run_all_simulations(weapon, mod_data, mod_data_exilus)
        return sim_results
        
    def run_all_simulations(self, weapon, mod_data, mod_data_exilus):
        exilus_options = [None] + mod_data_exilus

        # split locked vs free mods
        locked_mods, free_mods = self.split_locked_mods(mod_data)
        locked_count = len(locked_mods)

        if locked_count > 8:
            raise ValueError("More locked mods than available slots")

        remaining_slots = 8 - locked_count

        # Generate all regular mod combinations for the chosen range
        min_mods = max(0, min(self.minimum_simulated_mods, remaining_slots))
        combo_range = range(min_mods, remaining_slots + 1)
        regular_combos = chain.from_iterable(
            combinations(free_mods, r) for r in combo_range
        )

        # Calculate total for progress display
        display_total = (
            sum(comb(len(free_mods), r) for r in combo_range)
            * len(exilus_options)
        ) / self.progress_display_mod

        count = 0
        weapon_data_dict = {} # modded weapon stats hash -> results hash
        results_dict = {}  # results hash -> grouped data

        for regular_mods in regular_combos:
            # Always include locked mods
            full_mods = locked_mods + list(regular_mods)

            # Preserve original duplicate-name guard
            if len(full_mods) != len({mod["name"] for mod in full_mods}):
                continue

            if count % self.progress_display_mod == 0:
                print(f"Simulation: {int(count/self.progress_display_mod)}/{int(display_total)} (*{self.progress_display_mod})")

            for exilus_mod in exilus_options:
                self.run_simulation(weapon_data_dict, results_dict, weapon, full_mods, exilus_mod)

            count += 1

        print("Simulations Complete")
        return results_dict

    def hash_dict(self, data):
        # Deterministic serialization
        hash_bytes = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":")
        ).encode("utf-8")
        return hashlib.blake2b(hash_bytes, digest_size=16).hexdigest() # blake2b is faster than sha256 and perfect for this use case

    def run_simulation(self, weapon_dict, results_dict, weapon, mods, utility_mod):
        if utility_mod:
            mods = mods + [utility_mod]  # avoid mutating caller list

        # Get modded weapon values
        modded_weapon_values = {
            "base": self.get_modded_weapon_values(weapon, mods, False),
            "reloaded": self.get_modded_weapon_values(weapon, mods, True)
        }

        # Get mod names to use from this point onward
        mod_names = [mod["uniqueName"] for mod in mods]

        # Check if duplicate weapon stats and skip simulation if we can
        weapon_hash = self.hash_dict(modded_weapon_values)
        if weapon_hash in weapon_dict:
            results_dict[weapon_dict[weapon_hash]]["Mod Sets"].append(mod_names)
            return

        # Complete simulation and add results
        results = self.get_status_proc_data_over_time(modded_weapon_values)

        # Check hash for grouping 
        results_hash = self.hash_dict(results)
        if results_hash in results_dict:
            results_dict[results_hash]["Mod Sets"].append(mod_names)
        else:
            results_dict[results_hash] = {
                "Mod Sets": [mod_names],
                "Results": results
            }

        # Store weapon set to save simulations
        weapon_dict[weapon_hash] = results_hash

    def split_locked_mods(self, mods):
        locked = []
        free = []

        for mod in mods:
            if mod["name"].lower() in self.locked_mod_names:
                locked.append(mod)
            else:
                free.append(mod)

        return locked, free

    def get_modded_weapon_values(self, weapon, mods, reloaded):
        mod_sum_values = self.sum_relevant_mod_stats(mods, reloaded)
        modded_weapon_values = {
            "Fire Rate": weapon["fireRate"],
            "Multishot": weapon["multishot"],
            "Status Chance": weapon["attacks"][WEAPON_ATTACK]["status_chance"],
            "Reload Speed": weapon["reloadTime"],
            "Magazine Capacity": weapon["magazineSize"],
        }

        for status in modded_weapon_values:
            if status in mod_sum_values and mod_sum_values[status]["percent"]:
                modded_weapon_values[status] *= 1+mod_sum_values[status]["total"]/100
        for status in modded_weapon_values:
            if status in mod_sum_values and not mod_sum_values[status]["percent"]:
                modded_weapon_values[status] += mod_sum_values[status]["total"]
        return modded_weapon_values

    def get_status_proc_data_over_time(self, modded_weapon_values):
        def weapon_values():
            if reloaded: 
                return modded_weapon_values["reloaded"]
            return modded_weapon_values["base"]

        # Simulate fire
        sim_time = 0
        current_procs = 0
        sim_results = []
        reloaded = False
        sim_mag = weapon_values()["Magazine Capacity"]
        while sim_time <= self.max_burst_seconds:
            firing_time = 1 / weapon_values()["Fire Rate"]
            result = {"time": sim_time}
            if sim_mag > 0:
                result["action"] = "Fire"
                current_procs += weapon_values()["Multishot"] * weapon_values()["Status Chance"]
                sim_time += firing_time
                sim_mag -= 1
            else:
                reloaded = True
                result["action"] = "Reload"
                sim_time += weapon_values()["Reload Speed"]
                sim_mag = weapon_values()["Magazine Capacity"]
        
            result["procs"] = current_procs
            sim_results.append(result)
        return sim_results

    def sum_relevant_mod_stats(self, mods, reloaded):
        mod_sum_values = {}

        for mod in mods:
            for stat in mod["stats"]:
                if stat["condition"] == "On Reload" and not reloaded:
                    continue

                name = stat["name"]
                value_str = stat["value"]

                # Only sum relevant stats
                if any(rel_stat.lower() in name.lower() for rel_stat in RELEVANT_MOD_STATS):
                    # Parse the number and detect %
                    match = re.match(r'([+-]?[0-9.]+)(%?)', value_str)
                    if not match:
                        raise ValueError(f"Non-numeric stat value found: {value_str}")
                    
                    num, is_percent = match.groups()
                    num = float(num)
                    key = name.strip()

                    # Initialize if first time
                    if key not in mod_sum_values:
                        mod_sum_values[key] = {"total": 0.0, "percent": bool(is_percent)}

                    # Check consistency: can't mix % and raw numbers
                    if mod_sum_values[key]["percent"] != bool(is_percent):
                        raise ValueError(f"Inconsistent stat type for {key}: mixed % and raw numbers")

                    # Add to running total
                    mod_sum_values[key]["total"] += num

        return mod_sum_values

    def get_relevant_mods(self, mods, weapon):
        results = []
        results_utility = []
        for mod in mods:
            # Ignore mods
            if not self.is_player_facing_mod(mod): continue
            if not "compatName" in mod or weapon["type"] != mod["compatName"]: continue
            if any(mod["name"].lower().startswith(variant.lower()) for variant in VARIANTS_TO_STRIP): continue
            if any(variant.lower() in mod["wikiaUrl"].lower() for variant in VARIANTS_TO_STRIP): continue

            # Skip base mod if a Primed variant exists
            if not mod.get("isPrime"): 
                skip_mod = False
                for mod2 in mods:
                    if mod2.get("isPrime") and mod2["name"] == f"Primed {mod["name"]}":
                        skip_mod = True
                        break
                if skip_mod:
                    continue 

            # Get relevant data in new structure
            new_mod = {}

            # Copy some values
            keys_to_copy = ["name", "uniqueName", "wikiaUrl"]
            for key in keys_to_copy:
                new_mod[key] = mod[key]

            # Get maxed stats
            new_mod["stats"] = self.parse_maxed_stats(mod)

            # Only keep mods with relevant stats
            if not any(
                any(rel_stat.lower() in stat['name'].lower() for rel_stat in RELEVANT_MOD_STATS)
                for stat in new_mod["stats"]
            ): continue

            # Add to results
            if "isUtility" in mod and mod["isUtility"]:
                results_utility.append(new_mod)
            else:
                results.append(new_mod)

        return results, results_utility

    def parse_maxed_stats(self, mod):
        """
        Returns a list of dicts for maxed stats:
        [{name: ..., value: ..., condition: ...}, ...]
        - condition: optional prefix ending with ':'
        - value: first number found in the stat string (keeps +,-,%)
        - name: rest of the string cleaned up
        """
        max_level = mod["levelStats"][-1]["stats"]
        results = []

        for stat in max_level:
            # Clean escaped and actual newlines
            stat_clean = stat.replace('\\n', ' ').replace('\n', ' ').strip()

            # Extract optional condition prefix (before ':')
            cond_match = re.match(r'^(.*?):\s*(.*)', stat_clean)
            if cond_match:
                condition, rest = cond_match.groups()
            else:
                condition, rest = None, stat_clean

            # Ignore some conditions
            if condition and condition not in RELEVANT_CONDITIONS:
                continue

            # Extract first number (with optional +,-,%)
            num_match = re.search(r'([+-]?[0-9.]+%?)', rest)
            if num_match:
                value = num_match.group(1)
                # Remove number from text to get clean name
                name = (rest[:num_match.start()] + rest[num_match.end():]).strip()
            else:
                value = None
                name = rest.strip()

            results.append({
                "name": name,
                "value": value,
                "condition": condition
            })

        return results

    def get_weapon(self, data, name):
        weapons = [item for item in data if item["name"] == name]
        if len(weapons) != 1:
            raise ValueError(f"Expected 1 weapon with name {name}, found {len(weapons)}.")
        return weapons[0]

    def key_missing_or_falsy(self, obj, key):
        if key not in obj: return True
        if not obj[key]: return True
        return False

    def is_player_facing_mod(self, mod):
        required_keys = ["releaseDate", "wikiAvailable", "wikiaUrl"]
        return all(mod.get(k) for k in required_keys)

    def setup_cache(self):
        requests_cache.install_cache(
            cache_name="wf_cache",
            backend="sqlite",
            expire_after=CACHE_LIFESPAN
        )
