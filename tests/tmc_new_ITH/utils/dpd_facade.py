"""Dish Pointing Device Facade
"""

import tango


class DishPointingDevicesFacade:
    """A facade to expose the Dish Pointing Devices to the tests."""

    def __init__(self) -> None:
        self._dish_pointing_device_dict = {
            "SKA001": tango.DeviceProxy("mid-tmc/dish-pointing/ska001"),
            "SKA100": tango.DeviceProxy("mid-tmc/dish-pointing/ska100"),
            "SKA077": tango.DeviceProxy("mid-tmc/dish-pointing/ska077"),
            "SKA036": tango.DeviceProxy("mid-tmc/dish-pointing/ska036"),
        }

    @property
    def dish_pointing_device_dict(self) -> dict[str, tango.DeviceProxy]:
        """The dish pointing Tango device proxies as a dictionary.

        The key is the dish name, as a string in the format "dish_XXX".
        """
        return self._dish_pointing_device_dict

    @property
    def dish_pointing_device_list(self) -> list[tango.DeviceProxy]:
        """The dish pointing Tango device proxies as a list."""
        return list(self._dish_pointing_device_dict.values())
