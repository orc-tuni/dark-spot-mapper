"""This module provides custom exceptions for ORC Dark Spot Mapper"""

__author__ = "Mika Mäki"
__copyright__ = "Copyright 2016-2019, Tampere University"
__credits__ = ["Mika Mäki"]
__maintainer__ = "Mika Mäki"
__email__ = "mika.maki@tuni.fi"


class AbortException(Exception):
    """
    The purpose of this exception is to stop measurement threads when the abort button is clicked
    """
    pass
