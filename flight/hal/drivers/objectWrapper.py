from hal.drivers.errors import Errors


class objectWrapper:
    def __init__(self, obj):
        self.obj = obj
        self.fnError = False

    def __getattr__(self, name):
        if isinstance(self.obj, objectWrapper):
            self.fnError = True
            raise RuntimeError(f"Error: Recursive access detected for '{name}'")
        try:
            attr = getattr(self.obj, name)
            if callable(attr):  # Check if the attribute is a method

                def wrapped_method(*args, **kwargs):
                    try:
                        return attr(*args, **kwargs)
                    except Exception as e:
                        self.fnError = True
                        raise RuntimeError(f"Error calling method '{name}': {e}")

                return wrapped_method
            return attr
        except Exception as e:
            self.fnError = True
            raise RuntimeError(f"Error accessing attribute '{name}': {e}")

    ######################## ERROR HANDLING ########################

    @property
    def device_errors(self):
        result = self.obj.device_errors
        if self.fnError:
            result.append(Errors.FN_CALL_ERROR)
        return result
