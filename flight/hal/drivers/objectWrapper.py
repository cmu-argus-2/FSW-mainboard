from hal.drivers.errors import Errors


class objectWrapper:
    def __init__(self, obj):
        self.obj = obj
        self.fnError = False

    def __getattr__(self, name):
        if isinstance(self.obj, objectWrapper):
            self.fnError = True
            print(f"Error: Recursive access detected for '{name}'")
            return None
        try:
            return getattr(self.obj, name)
        except Exception as e:
            self.fnError = True
            print(f"Error accessing attribute '{name}': {e}")
            return None

    ######################## ERROR HANDLING ########################

    @property
    def device_errors(self):
        result = self.obj.device_errors
        if self.fnError:
            result.append(Errors.FN_CALL_ERROR)
        return result
