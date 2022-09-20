# Copyright (C) 2022 Radiotherapy AI Holdings Pty Ltd

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Module for generating DICOM files from a dictionary format"""

from typing import Any, Optional, Union, cast

import numpy as np
import pydicom
import pydicom.datadict
from numpy.typing import NDArray

DicomItem = Union[
    dict[str, "DicomItem"],
    list[dict[str, "DicomItem"]],
    list[float],
    list[str],
    list[int],
    NDArray[Any],
]


def append_dict_to_dataset(
    to_append: dict[str, DicomItem], ds: Optional[pydicom.Dataset] = None
):
    """Append a dictionary to a given pydicom Dataset

    Parameters
    ----------
    to_append : dict[str, DicomItem]
        A dictionary in the structure of a DICOM header.
    ds : Optional[pydicom.Dataset], optional
        The pydicom Dataset for which to append the dictionary to. If
        left unset, a new Dataset is created.

    Returns
    -------
    pydicom.Dataset
        The combined Dataset

    Examples
    --------
    >>> ds = append_dict_to_dataset({
    ...    "PatientName": "MacDonald^George",
    ... })
    >>> ds.PatientName
    'MacDonald^George'

    """

    if ds is None:
        ds = pydicom.Dataset()

    for key, value in to_append.items():
        if key not in pydicom.datadict.keyword_dict.keys():
            raise ValueError(f"{key} is not within the DICOM dictionary.")

        if isinstance(value, dict):
            setattr(ds, key, append_dict_to_dataset(value, pydicom.Dataset()))

        elif isinstance(value, list):
            if all(not isinstance(item, dict) for item in value):
                _add_item_to_dataset(ds, key, value)

            elif all(isinstance(item, dict) for item in value):
                vr = _get_vr(key)
                if vr != "SQ":
                    raise ValueError(
                        "In order to provide a list of dictionaries to "
                        f"{key}, it needs to have a VR of SQ. However "
                        f"VR was {vr}."
                    )

                value = cast(list[dict[str, DicomItem]], value)

                setattr(
                    ds,
                    key,
                    [append_dict_to_dataset(item, pydicom.Dataset()) for item in value],
                )

            else:
                raise ValueError(
                    f"{key} should contain either only dictionaries, or no "
                    "dictionaries"
                )
        else:
            _add_item_to_dataset(ds, key, value)

    return ds


def _get_vr(key: str):
    tag = pydicom.datadict.keyword_dict[key]
    vr = pydicom.datadict.dictionary_VR(tag)

    return vr


def _add_item_to_dataset(dataset: pydicom.Dataset, key: str, value: DicomItem):
    if isinstance(value, np.ndarray):
        value = value.tolist()

    setattr(dataset, key, value)
