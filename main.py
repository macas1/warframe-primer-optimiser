from weapon_simulator import WeaponSimulator
from sim_results_scorer import SimResultsScorer
from sim_results_grapher import SimResultsGrapher
from pprint import pprint
import json
import heapq

MAX_RESULTS = 50

def main():
    # Do simulations ---------------------------------
    sim_results, sim_mods = WeaponSimulator(
        weapon_name="Kompressa Prime",
        max_burst_seconds=12,
        progress_display_mod=1000,
        locked_mod_names=["Anemic Agility", "Barrel Diffusion", "Lethal Torrent"],
    ).run()
    pprint(len(sim_results))

    # Score simulations ---------------------------------
    score_items = SimResultsScorer.scoreResults(
        sim_results=sim_results,
        max_results=MAX_RESULTS
    )

    selected_ids = {result_id for item in score_items for _, result_id in item["heap"]}
    selected_results = [sim_results[result_id] for result_id in selected_ids]

    # Graph Simulations --------------------------------
    grapher = SimResultsGrapher()
    grapher.graph(
        selected_results,
        sim_mods
    )


if __name__ == "__main__":
    main()