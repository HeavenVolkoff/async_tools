class BasicRepr:
    def __str__(self) -> str:
        return str(type(self).__qualname__)

    def __repr__(self) -> str:
        return (
            "<{}: ".format(type(self).__qualname__)
            + (
                ", ".join(
                    [
                        "{}={}".format(key, repr(val))
                        for key, val in vars(self).items()
                        if not key.startswith("_")
                    ]
                )
            )
            + ">"
        )
