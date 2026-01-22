from weapon_simulator import WeaponSimulator
from sim_results_scorer import SimResultsScorer
from sim_results_grapher import SimResultsGrapher
from pprint import pprint

# TODO: Draw order matters? Higher scoring on top?
# TODO: GUI?

MAX_RESULTS = 100
MAX_BURST_SECONDS = 12

def main():
    # Do simulations --------------------------------------
    sim_results, sim_mods = WeaponSimulator(
        weapon_name="Grimoire",
        max_burst_seconds=MAX_BURST_SECONDS,
        progress_display_mod=10000,
        minimum_simulated_mods=8,
        locked_mod_names=[]
    ).run()
    pprint(len(sim_results))

    # Score simulations -----------------------------------
    score_items = SimResultsScorer.scoreResults(
        sim_results=sim_results,
        max_results=MAX_RESULTS
    )

    selected_ids = {result_id for item in score_items for _, result_id in item["heap"]}
    selected_results = [sim_results[result_id] for result_id in selected_ids]

    # Ground selected results to graph nicer --------------
    for result in selected_results:
        if result["Results"][0]["time"] > 0:
            result["Results"].insert(0, {"action": "Idle", "time": 0, "procs": 0})

    # Graph Simulations -----------------------------------
    grapher = SimResultsGrapher()
    grapher.graph(
        selected_results,
        sim_mods,
        MAX_BURST_SECONDS
    )


if __name__ == "__main__":
    main()