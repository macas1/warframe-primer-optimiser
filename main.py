from weapon_simulator import WeaponSimulator
from sim_results_scorer import SimResultsScorer
from pprint import pprint
import json
import heapq

TOP_SIMULATION_COUNT = 20

def main():
    # Do simulations ---------------------------------
    sim_results = WeaponSimulator(
        weapon_name="Kompressa Prime",
        max_burst_seconds=12,
        progress_display_mod=1000,
        locked_mod_names=["Anemic Agility", "Barrel Diffusion", "Lethal Torrent"],
    ).run()
    pprint(len(sim_results))

    # Score simulations ---------------------------------
    score_items = [
        {
            "name": "Average/Sec",
            "function": SimResultsScorer.score_average_per_sec,
            "heap": []
        },
        {
            "name": "Total",
            "function": SimResultsScorer.score_total,
            "heap": []
        },
    ]
    SimResultsScorer.scoreResults(
        score_items=score_items,
        sim_results=sim_results,
        result_count=TOP_SIMULATION_COUNT
    )

    # Print scores (TEMP)
    for score_item in score_items:
        for score, result_id in heapq.nlargest(len(score_item["heap"]), score_item["heap"]):
            pprint(f"{result_id} {score_item["name"]} {score}")


if __name__ == "__main__":
    main()