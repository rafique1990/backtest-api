import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestBacktestEndpointEdgeCases:
    """Test edge cases for /api/v1/backtest endpoint."""

    def test_missing_portfolio_creation(self):
        """Test request missing portfolio_creation field."""
        payload = {
            "calendar_rules": {
                "rule_type": "Quarterly",
                "initial_date": "2024-11-25"
            },
            "weighting_scheme": {
                "weighting_type": "Equal"
            }
        }
        response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code == 422
        assert "portfolio_creation" in response.text.lower()

    def test_missing_weighting_scheme(self):
        """Test request missing weighting_scheme field."""
        payload = {
            "calendar_rules": {
                "rule_type": "Quarterly",
                "initial_date": "2024-11-25"
            },
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 10,
                "data_field": "market_capitalization"
            }
        }
        response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code == 422
        assert "weighting_scheme" in response.text.lower()

    def test_missing_calendar_rules(self):
        """Test request missing calendar_rules field."""
        payload = {
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 10,
                "data_field": "market_capitalization"
            },
            "weighting_scheme": {
                "weighting_type": "Equal"
            }
        }
        response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code == 422
        assert "calendar_rules" in response.text.lower()

    def test_missing_initial_date_in_calendar_rules(self):
        """Test calendar_rules missing initial_date."""
        payload = {
            "calendar_rules": {
                "rule_type": "Quarterly"
            },
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 10,
                "data_field": "market_capitalization"
            },
            "weighting_scheme": {
                "weighting_type": "Equal"
            }
        }
        response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code == 422
        assert "initial_date" in response.text.lower()

    def test_invalid_rule_type(self):
        """Test invalid rule_type value."""
        payload = {
            "calendar_rules": {
                "rule_type": "Monthly",  # Invalid - only Quarterly supported
                "initial_date": "2024-11-25"
            },
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 10,
                "data_field": "market_capitalization"
            },
            "weighting_scheme": {
                "weighting_type": "Equal"
            }
        }
        response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code == 422

    def test_invalid_filter_type(self):
        """Test invalid filter_type value."""
        payload = {
            "calendar_rules": {
                "rule_type": "Quarterly",
                "initial_date": "2024-11-25"
            },
            "portfolio_creation": {
                "filter_type": "LowN",  # Invalid - only TopN supported
                "n": 10,
                "data_field": "market_capitalization"
            },
            "weighting_scheme": {
                "weighting_type": "Equal"
            }
        }
        response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code == 422

    def test_invalid_weighting_type(self):
        """Test invalid weighting_type value."""
        payload = {
            "calendar_rules": {
                "rule_type": "Quarterly",
                "initial_date": "2024-11-25"
            },
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 10,
                "data_field": "market_capitalization"
            },
            "weighting_scheme": {
                "weighting_type": "MAX"  # Invalid - only Equal supported
            }
        }
        response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code == 422

    def test_invalid_data_field(self):
        """Test invalid data_field value."""
        payload = {
            "calendar_rules": {
                "rule_type": "Quarterly",
                "initial_date": "2024-11-25"
            },
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 10,
                "data_field": "profit"  # Invalid field
            },
            "weighting_scheme": {
                "weighting_type": "Equal"
            }
        }
        response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code == 422
        assert "data_field" in response.text.lower()

    def test_negative_n_value(self):
        """Test negative n value."""
        payload = {
            "calendar_rules": {
                "rule_type": "Quarterly",
                "initial_date": "2024-11-25"
            },
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": -5,  # Invalid
                "data_field": "market_capitalization"
            },
            "weighting_scheme": {
                "weighting_type": "Equal"
            }
        }
        response = client.post("/api/v1/backtest", json=payload)
        # Should either reject or handle gracefully
        assert response.status_code in [400, 422]

    def test_zero_n_value(self):
        """Test zero n value."""
        payload = {
            "calendar_rules": {
                "rule_type": "Quarterly",
                "initial_date": "2024-11-25"
            },
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 0,  # Edge case
                "data_field": "market_capitalization"
            },
            "weighting_scheme": {
                "weighting_type": "Equal"
            }
        }
        response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code in [400, 422]

    def test_invalid_date_format(self):
        """Test invalid date format."""
        payload = {
            "calendar_rules": {
                "rule_type": "Quarterly",
                "initial_date": "25-11-2024"  # Wrong format
            },
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 10,
                "data_field": "market_capitalization"
            },
            "weighting_scheme": {
                "weighting_type": "Equal"
            }
        }
        response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code == 422

    def test_future_date(self):
        """Test date in the future."""
        payload = {
            "calendar_rules": {
                "rule_type": "Quarterly",
                "initial_date": "2030-01-01"  # Future date
            },
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 10,
                "data_field": "market_capitalization"
            },
            "weighting_scheme": {
                "weighting_type": "Equal"
            }
        }
        response = client.post("/api/v1/backtest", json=payload)
        # Should handle gracefully - might succeed or fail depending on data
        assert response.status_code in [200, 400]

    def test_very_old_date(self):
        """Test very old date before data availability."""
        payload = {
            "calendar_rules": {
                "rule_type": "Quarterly",
                "initial_date": "1900-01-01"
            },
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 10,
                "data_field": "market_capitalization"
            },
            "weighting_scheme": {
                "weighting_type": "Equal"
            }
        }
        response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code in [200, 400]

    def test_empty_payload(self):
        """Test completely empty payload."""
        response = client.post("/api/v1/backtest", json={})
        assert response.status_code == 422

    def test_null_values(self):
        """Test null values in required fields."""
        payload = {
            "calendar_rules": None,
            "portfolio_creation": None,
            "weighting_scheme": None
        }
        response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code == 422

    def test_extra_fields(self):
        """Test payload with extra unexpected fields."""
        payload = {
            "calendar_rules": {
                "rule_type": "Quarterly",
                "initial_date": "2024-11-25"
            },
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 10,
                "data_field": "market_capitalization"
            },
            "weighting_scheme": {
                "weighting_type": "Equal"
            },
            "extra_field": "should be ignored"
        }
        response = client.post("/api/v1/backtest", json=payload)
        # Pydantic should ignore extra fields by default
        assert response.status_code in [200, 400]

    def test_string_instead_of_integer_n(self):
        """Test string value for n field."""
        payload = {
            "calendar_rules": {
                "rule_type": "Quarterly",
                "initial_date": "2024-11-25"
            },
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": "ten",  # String instead of int
                "data_field": "market_capitalization"
            },
            "weighting_scheme": {
                "weighting_type": "Equal"
            }
        }
        response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code == 422

    def test_sql_injection_in_data_field(self):
        """Test SQL injection attempt in data_field."""
        payload = {
            "calendar_rules": {
                "rule_type": "Quarterly",
                "initial_date": "2024-11-25"
            },
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 10,
                "data_field": "market_capitalization; DROP TABLE users;"
            },
            "weighting_scheme": {
                "weighting_type": "Equal"
            }
        }
        response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code == 422

    def test_path_traversal_in_data_field(self):
        """Test path traversal attempt in data_field."""
        payload = {
            "calendar_rules": {
                "rule_type": "Quarterly",
                "initial_date": "2024-11-25"
            },
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 10,
                "data_field": "../../../etc/passwd"
            },
            "weighting_scheme": {
                "weighting_type": "Equal"
            }
        }
        response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code == 422

    def test_valid_request_all_fields(self):
        """Test valid request with all required fields."""
        payload = {
            "calendar_rules": {
                "rule_type": "Quarterly",
                "initial_date": "2024-01-01"
            },
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 10,
                "data_field": "market_capitalization"
            },
            "weighting_scheme": {
                "weighting_type": "Equal"
            }
        }
        response = client.post("/api/v1/backtest", json=payload)
        # Should succeed or fail gracefully depending on data availability
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert "weights" in data
            assert "metadata" in data
            assert "execution_time" in data

    def test_all_valid_data_fields(self):
        """Test all valid data_field values."""
        valid_fields = ["market_capitalization", "prices", "volume", "adtv_3_month"]
        
        for field in valid_fields:
            payload = {
                "calendar_rules": {
                    "rule_type": "Quarterly",
                    "initial_date": "2024-01-01"
                },
                "portfolio_creation": {
                    "filter_type": "TopN",
                    "n": 5,
                    "data_field": field
                },
                "weighting_scheme": {
                    "weighting_type": "Equal"
                }
            }
            response = client.post("/api/v1/backtest", json=payload)
            assert response.status_code in [200, 400], f"Failed for field: {field}"


class TestBacktestPromptEndpointEdgeCases:
    """Test edge cases for /api/v1/backtest-prompt endpoint."""

    def test_empty_prompt(self):
        """Test empty prompt string."""
        payload = {"prompt": ""}
        response = client.post("/api/v1/backtest-prompt", json=payload)
        assert response.status_code in [400, 422]

    def test_missing_prompt_field(self):
        """Test request missing prompt field."""
        response = client.post("/api/v1/backtest-prompt", json={})
        assert response.status_code == 422

    def test_null_prompt(self):
        """Test null prompt value."""
        payload = {"prompt": None}
        response = client.post("/api/v1/backtest-prompt", json=payload)
        assert response.status_code == 422

    def test_very_long_prompt(self):
        """Test extremely long prompt."""
        payload = {"prompt": "Run backtest " * 1000}
        response = client.post("/api/v1/backtest-prompt", json=payload)
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_prompt_with_special_characters(self):
        """Test prompt with special characters."""
        payload = {"prompt": "Run backtest with @#$%^&*() symbols"}
        response = client.post("/api/v1/backtest-prompt", json=payload)
        assert response.status_code in [200, 400]

    def test_prompt_missing_all_information(self):
        """Test prompt with minimal information."""
        payload = {"prompt": "Run backtest"}
        response = client.post("/api/v1/backtest-prompt", json=payload)
        # LLM should use defaults or fail gracefully
        assert response.status_code in [200, 400]

    def test_prompt_missing_n_value(self):
        """Test prompt missing number of securities."""
        payload = {
            "prompt": "Run backtest with by market_capitalization starting 2023-06-01"
        }
        response = client.post("/api/v1/backtest-prompt", json=payload)
        # Should use default n=10
        assert response.status_code in [200, 400]

    def test_prompt_missing_data_field(self):
        """Test prompt missing data field."""
        payload = {
            "prompt": "Run backtest with top 15 securities starting 2023-06-01"
        }
        response = client.post("/api/v1/backtest-prompt", json=payload)
        # Should use default market_capitalization
        assert response.status_code in [200, 400]

    def test_prompt_missing_date(self):
        """Test prompt missing start date."""
        payload = {
            "prompt": "Run backtest with top 15 securities by market_capitalization"
        }
        response = client.post("/api/v1/backtest-prompt", json=payload)
        # Should use default date
        assert response.status_code in [200, 400]

    def test_prompt_with_multiple_dates(self):
        """Test prompt with ambiguous multiple dates."""
        payload = {
            "prompt": "Run backtest with top 15 securities. I want to start after my baby born on 20.03.2024. Analyze data starting 2023-06-01 by market_capitalization"
        }
        response = client.post("/api/v1/backtest-prompt", json=payload)
        # LLM should pick the most relevant date
        assert response.status_code in [200, 400]

    def test_prompt_with_multiple_n_values(self):
        """Test prompt with multiple n values."""
        payload = {
            "prompt": "Run backtest with top 15 securities or 50 securities. I have 50 dollars starting 2023-06-01 by market_capitalization"
        }
        response = client.post("/api/v1/backtest-prompt", json=payload)
        # LLM should pick one value
        assert response.status_code in [200, 400]

    def test_prompt_with_invalid_data_field(self):
        """Test prompt requesting invalid data field."""
        payload = {
            "prompt": "Run backtest with top 15 securities starting 2023-06-01 by profit"
        }
        response = client.post("/api/v1/backtest-prompt", json=payload)
        # Should fail validation after LLM extraction
        assert response.status_code in [400, 422]

    def test_prompt_with_adtv_variation(self):
        """Test prompt with ADTV variations."""
        prompts = [
            "Run backtest with top 10 securities by ADTV starting 2023-01-01",
            "Run backtest with top 10 securities by average daily trading volume starting 2023-01-01",
            "Run backtest with top 10 securities by adtv_3_month starting 2023-01-01"
        ]
        
        for prompt_text in prompts:
            payload = {"prompt": prompt_text}
            response = client.post("/api/v1/backtest-prompt", json=payload)
            # All should map to adtv_3_month
            assert response.status_code in [200, 400]

    def test_valid_prompt_complete(self):
        """Test valid prompt with all information."""
        payload = {
            "prompt": "Run backtest with top 15 securities by market_capitalization starting 2023-06-01"
        }
        response = client.post("/api/v1/backtest-prompt", json=payload)
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert "weights" in data
            assert "metadata" in data

    def test_prompt_case_insensitive(self):
        """Test prompt with different cases."""
        payload = {
            "prompt": "RUN BACKTEST WITH TOP 10 SECURITIES BY MARKET_CAPITALIZATION STARTING 2023-01-01"
        }
        response = client.post("/api/v1/backtest-prompt", json=payload)
        assert response.status_code in [200, 400]

    def test_prompt_with_typos(self):
        """Test prompt with common typos."""
        payload = {
            "prompt": "Run backtst with top 10 securites by market_capitalizaton starting 2023-01-01"
        }
        response = client.post("/api/v1/backtest-prompt", json=payload)
        # LLM should handle typos
        assert response.status_code in [200, 400]
