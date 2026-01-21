from weapon_simulator import WeaponSimulator
from pprint import pprint


def main():
    sim_results = WeaponSimulator(
        weapon_name="Kompressa Prime",
        max_burst_seconds=12,
        locked_mod_names=["Anemic Agility", "Scorch", "Barrel Diffusion", "Lethal Torrent"],
    ).run()
    pprint(len(sim_results))


if __name__ == "__main__":
    main()