
def rule_based_strategy(record):
    actions = []

    if record["inventory"] < record["demand"]:
        actions.append("Replenish inventory")

    if record["supplier_reliability"] < 0.65:
        actions.append("Find alternative supplier")

    if record["weather_risk"] > 0.85:
        actions.append("Evaluate alternative route")

    return {
        "strategy": "rule_based",
        "recommendations": actions or ["Continue normal operations"]
    }


def predictive_strategy(record, prediction):
    actions = []

    if prediction["delay_probability"] >= 0.65:
        actions.append("Prepare alternative supplier")

    if record["inventory"] < record["demand"] * 1.2:
        actions.append("Calculate emergency reorder quantity")

    if record["weather_risk"] > 0.7:
        actions.append("Forecast alternative transportation route")

    return {
        "strategy": "predictive_ai",
        "recommendations": actions or ["Monitor shipment"]
    }


def multi_agent_strategy(record, prediction):
    supplier_agent = (
        "Find alternative supplier"
        if record["supplier_reliability"] < 0.75
        else "Continue current supplier"
    )

    inventory_agent = (
        "Transfer warehouse inventory"
        if record["inventory"] < record["demand"]
        else "Maintain current stock"
    )

    logistics_agent = (
        "Evaluate alternative route"
        if record["weather_risk"] > 0.7
        or prediction["delay_probability"] >= 0.65
        else "Maintain current route"
    )

    return {
        "strategy": "multi_agent",
        "agent_results": {
            "supplier_agent": supplier_agent,
            "inventory_agent": inventory_agent,
            "logistics_agent": logistics_agent
        },
        "recommendations": [
            supplier_agent,
            inventory_agent,
            logistics_agent
        ]
    }
