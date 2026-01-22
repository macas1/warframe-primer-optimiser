import heapq

class SimResultsScorer:
    @staticmethod
    def scoreResults(sim_results, max_results):
        score_items = [
            {
                "name": "Total",
                "function": SimResultsScorer.score_total,
            },
            {
                "name": "Average/Sec",
                "function": SimResultsScorer.score_average_per_sec,
            },
            {
                "name": "First Mag Total",
                "function": SimResultsScorer.score_first_mag,
            },
            {
                "name": "First Mag Average/Sec",
                "function": SimResultsScorer.score_first_mag_average_per_sec,
            },
            {
                "name": "First Bullet",
                "function": SimResultsScorer.score_first_bullet,
            },
            
        ]

        for score_item in score_items:
            score_item["heap"] = []
        
        result_count = int(max_results/len(score_items))
        for result_id, results in sim_results.items():
            results["scores"] = []
            for score_item in score_items:
                score = score_item["function"](results)
                results["scores"].append((score_item["name"], score))
                if len(score_item["heap"]) < result_count:
                    heapq.heappush(score_item["heap"], (score, result_id))
                elif score > score_item["heap"][0][0]:
                    heapq.heapreplace(score_item["heap"], (score, result_id))
        return score_items

    @staticmethod
    def score_total(sim_result):
        final_entry = sim_result["Results"][-1]
        return final_entry["procs"]
    
    @staticmethod
    def score_average_per_sec(sim_result):
        final_entry = sim_result["Results"][-1]
        return final_entry["procs"]/final_entry["time"]

    @staticmethod
    def score_first_mag(sim_result):
        for result in sim_result["Results"]:
            if result["action"] == "Reload Start":
                return result["procs"]
        return SimResultsScorer.score_total(sim_result)
    
    @staticmethod
    def score_first_mag_average_per_sec(sim_result):
        for result in sim_result["Results"]:
            if result["action"] == "Reload Start":
                return result["procs"]/result["time"]
        return SimResultsScorer.score_average_per_sec(sim_result)
    
    @staticmethod
    def score_first_bullet(sim_result): 
        for result in sim_result["Results"]:
            if result["action"] == "Fire":
                return result["procs"]
        return 0