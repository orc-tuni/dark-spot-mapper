"""This module provides custom exceptions for ORC Dark Spot Mapper

Copyright 2016 - 2019 Mika Mäki & Tampere University of Technology
Mika would like to license this program with GPLv3+ but it would require some university bureaucracy
"""


class AbortException(Exception):
    """
    The purpose of this exception is to stop measurement threads when the abort button is clicked
    """
    pass
