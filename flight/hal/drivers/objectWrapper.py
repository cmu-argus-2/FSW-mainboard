from hal.drivers.errors import Errors


class objectWrapper:
    def __init__(self, obj):
        self.obj = obj
        self.fnError = False

    def __getattr__(self, name):
        try:
            return getattr(self.obj, name)
        except Exception:
            self.fnError = True
            return None

    ######################## ERROR HANDLING ########################

    @property
    def device_errors(self):
        result = self.obj.device_errors
        if self.fnError:
            result.append(Errors.FN_CALL_ERROR)
        return result
