import matplotlib.pyplot as plt

class SimResultsGrapher:
    @staticmethod 
    def graph(result_list, mod_map):
        _, ax = plt.subplots()

        for index, result in enumerate(result_list):
            times = [r["time"] for r in result["Results"]]
            procs = [r["procs"] for r in result["Results"]]
            ax.plot(times, procs, alpha=0.6, label=f"{index}")

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Total Procs")
        ax.set_title("Status Procs Over Time")
        ax.legend()
        plt.show()