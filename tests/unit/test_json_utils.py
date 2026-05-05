import pytest

from cadpilotv3.shared.json_utils import JSONExtractionError, parse_json


def test_parse_json_repairs_unquoted_numeric_expressions() -> None:
    data = parse_json(
        """
{
  "parameters": {
    "CABLE_OPEN_Y": {
      "value": -29.0,
      "unit": "mm",
      "description": "Cable opening Y position.",
      "min": -((60.0/2)-1.0),
      "max": -((60.0/2)-1.0),
      "depends_on": ["BASE_W"],
      "constraint": "must be -(BASE_W/2 - 1.0)",
      "is_derived": true,
      "derived_from": "-(BASE_W/2 - 1.0)"
    }
  }
}
"""
    )

    parameter = data["parameters"]["CABLE_OPEN_Y"]

    assert parameter["min"] == -29
    assert parameter["max"] == -29
    assert parameter["constraint"] == "must be -(BASE_W/2 - 1.0)"


def test_parse_json_does_not_evaluate_parameter_name_expressions() -> None:
    with pytest.raises(JSONExtractionError):
        parse_json(
            """
{
  "parameters": {
    "INNER_W": {
      "value": BASE_W - 2.0
    }
  }
}
"""
        )
