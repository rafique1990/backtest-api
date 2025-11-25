import pytest
from app.utils.validators import validate_data_field


class TestValidateDataField:
    """Test suite for data_field validator."""

    def test_valid_market_capitalization(self):
        """Test valid market_capitalization field."""
        result = validate_data_field("market_capitalization")
        assert result == "market_capitalization"

    def test_valid_prices(self):
        """Test valid prices field."""
        result = validate_data_field("prices")
        assert result == "prices"

    def test_valid_volume(self):
        """Test valid volume field."""
        result = validate_data_field("volume")
        assert result == "volume"

    def test_valid_adtv_3_month(self):
        """Test valid adtv_3_month field."""
        result = validate_data_field("adtv_3_month")
        assert result == "adtv_3_month"

    def test_invalid_field_raises_value_error(self):
        """Test that invalid field raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_data_field("invalid_field")
        
        assert "Invalid data_field: invalid_field" in str(exc_info.value)
        assert "market_capitalization" in str(exc_info.value)
        assert "prices" in str(exc_info.value)
        assert "volume" in str(exc_info.value)
        assert "adtv_3_month" in str(exc_info.value)

    def test_empty_string_raises_value_error(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_data_field("")
        
        assert "Invalid data_field" in str(exc_info.value)

    def test_case_sensitive(self):
        """Test that validation is case-sensitive."""
        with pytest.raises(ValueError):
            validate_data_field("Market_Capitalization")
        
        with pytest.raises(ValueError):
            validate_data_field("PRICES")

    def test_whitespace_not_allowed(self):
        """Test that fields with whitespace are rejected."""
        with pytest.raises(ValueError):
            validate_data_field("market capitalization")
        
        with pytest.raises(ValueError):
            validate_data_field(" prices")
        
        with pytest.raises(ValueError):
            validate_data_field("volume ")

    def test_partial_match_not_allowed(self):
        """Test that partial matches are not accepted."""
        with pytest.raises(ValueError):
            validate_data_field("market")
        
        with pytest.raises(ValueError):
            validate_data_field("adtv")

    def test_sql_injection_attempt(self):
        """Test that SQL injection attempts are rejected."""
        with pytest.raises(ValueError):
            validate_data_field("prices; DROP TABLE users;")

    def test_path_traversal_attempt(self):
        """Test that path traversal attempts are rejected."""
        with pytest.raises(ValueError):
            validate_data_field("../../../etc/passwd")
        
        with pytest.raises(ValueError):
            validate_data_field("..\\..\\windows\\system32")

    def test_special_characters_rejected(self):
        """Test that special characters are rejected."""
        invalid_inputs = [
            "prices@domain.com",
            "volume#123",
            "market$cap",
            "data%field",
            "field&name",
            "test*field",
        ]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(ValueError):
                validate_data_field(invalid_input)
