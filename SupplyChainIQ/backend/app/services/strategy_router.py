
from app.services.flagsmith_service import get_decision_strategy
from app.services.prediction_engine import predict_delay

from app.ai.strategies.decision_strategies import (
    rule_based_strategy,
    predictive_strategy,
    multi_agent_strategy
)

def execute_decision(record):

    strategy = get_decision_strategy()

    prediction = predict_delay(record)

    if strategy == "predictive_ai":
        result = predictive_strategy(record, prediction)

    elif strategy == "multi_agent":
        result = multi_agent_strategy(record, prediction)

    else:
        result = rule_based_strategy(record)

    return {
        "selected_strategy": strategy,
        "prediction": prediction,
        "decision": result
    }
