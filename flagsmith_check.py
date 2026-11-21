import os

from flagsmith import Flagsmith

flagsmith = Flagsmith(
    environment_key=os.environ["FLAGSMITH_ENVIRONMENT_KEY"],
)

# The method below triggers a network request
flags = flagsmith.get_environment_flags()

# Check whether the feature is enabled
is_enabled = flags.is_feature_enabled("my_cool_feature")
print("my_cool_feature enabled:", is_enabled)

# Or read its value
feature_value = flags.get_feature_value("banner_size")
print("banner_size value:", feature_value)
