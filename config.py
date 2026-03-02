# Global settings
FORECAST_HORIZON = 14  # default days
STAFF_COST_PER_DAY = 250
LOCATIONS = ["Shelter A", "Shelter B", "Shelter C"]
DEFAULT_SCENARIOS = [
    {"arrival_surge": 0, "discharge_delay": 0},
    {"arrival_surge": 20, "discharge_delay": 10}
]
STAFF_AVAILABILITY_PCT = 100
