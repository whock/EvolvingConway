# Fills in defaults to any missing value in x.
# Used for allowing the user to override certain arguments.
# It works recursively.
import copy
def fill(x, defaults):
    # shallow copy of all keys so that it does not modify x.
    # Be careful since it's only a shallow copy.
    y = copy.copy(x)
    for k in y:
        if not (k in y):
            y[k] = defaults[k]
        elif isinstance(y[k], dict) and isinstance(defaults[k], dict):
            y[k] = fill(y[k], defaults[k]) # recursive for dicts of dicts.