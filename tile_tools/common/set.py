class CapturingSet(set):
    """A `set` that keeps track of all of its changes.

    Can be swapped in for a normal set, but has worse performance and takes up
    a lot of space.

    Useful for debugging and rendering the algorithm.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # List to keep snapshots
        self.log = [set()]

    # Methods that mutate the set
    methods = (
        "__isub__",
        "__ior__",
        "__iand__",
        "__ixor__",
        "add",
        "update",
        "pop",
        "remove",
        "discard",
        "clear",
        "intersection_update",
        "difference_update",
        "symmetric_difference_update",
    )

    # Wrap all mutating methods with captured call.
    for m in methods:
        locals()[m] = lambda self, *args, __f=m, **kwargs: self._call_with_capture(
            object.__getattribute__(set, __f), *args, **kwargs
        )

    def _call_with_capture(self, __f, *args, **kwargs):
        """Call `__f` and take a snapshot of the set afterwards.

        Args:
            __f - The function to call
            *args - Any of the function's args
            **kwargs - Any of the functions kwargs

        Returns:
            Anything the wrapped function returns.
        """
        result = __f(self, *args, **kwargs)
        self.log.append(self.copy())
        return result
