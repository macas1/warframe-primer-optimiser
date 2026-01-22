import matplotlib.pyplot as plt
from pprint import pprint

class SimResultsGrapher:
    @staticmethod 
    def graph(result_list, mod_map):
        fig, ax = plt.subplots()

        # Create lines
        lines = []
        for index, result in enumerate(result_list):
            times = [r["time"] for r in result["Results"]]
            procs = [r["procs"] for r in result["Results"]]
            line, = ax.plot(times, procs, alpha=0.6, label=f"{index}", picker=2)
            lines.append((line, result))  # store line and data

        # Create metadata
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Total Procs")
        ax.set_title("Status Procs Over Time")

        # Events
        def on_pick(event):
            line = event.artist
            for l, result in lines:
                if l == line:
                    SimResultsGrapher.on_selected(l, result, mod_map)
                    break

        # Apply and draw
        fig.canvas.mpl_connect('pick_event', on_pick)
        plt.show()

    @staticmethod
    def on_selected(line, result, mod_map):
        # Collect common mods
        common_mods, dynamic_sets = SimResultsGrapher.split_common_mods(result["Mod Sets"])
        
        print(f"\n\nClicked on: {line}")
        print("Common:")
        for mod_id in common_mods:
            print(f"    {mod_map[mod_id]["name"]}")

        for i, mod_set in enumerate(dynamic_sets):
            print(f"Other {i}:")
            for mod_id in mod_set:
                print(f"    {mod_map[mod_id]["name"]}")

    @staticmethod
    def split_common_mods(mod_sets):
        if not mod_sets: return [], []

        # Find mods present in every set
        common_mods = set(mod_sets[0])
        for mods in mod_sets[1:]:
            common_mods &= set(mods)

        # Remove common mods from each set
        stripped_mod_sets = [
            [mod for mod in mods if mod not in common_mods]
            for mods in mod_sets
        ]

        return list(common_mods), stripped_mod_sets