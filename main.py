from weapon_simulator import WeaponSimulator
from pprint import pprint


def main():
    sim_results = WeaponSimulator(
        weapon_name="Kompressa Prime",
        max_burst_seconds=12,
        locked_mod_names=["Anemic Agility", "Scorch", "Barrel Diffusion", "Lethal Torrent"],
    ).run()
    pprint(len(sim_results))

    # TODO: For each result Score it
    #   Average Procs/Sec calculated on final entry
    #   Total Procs in different burst periods
    # And then pick the top X results from BOTH sets and add them together


if __name__ == "__main__":
    main()