
import time
import uuid

EXPERIMENT_RESULTS = []

def record_experiment(record, decision_result):

    experiment = {
        "experiment_id": str(uuid.uuid4()),
        "shipment_id": record["shipment_id"],
        "strategy": decision_result["selected_strategy"],
        "recommendations": decision_result["decision"]["recommendations"],
        "prediction": decision_result["prediction"],
        "response_time": decision_result.get("response_time"),
        "actual_delay": record["actual_delay"],
        "shipping_cost": record["shipping_cost"]
    }

    EXPERIMENT_RESULTS.append(experiment)

    return experiment


def get_experiment_results():
    return EXPERIMENT_RESULTS
