import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import date

from app.main import app
from app.schemas import (
    BacktestRequest,
    CalendarRules,
    PortfolioCreation,
    WeightingScheme,
    PerformanceMetrics,
    StrategySummary,
)
from app.core.exceptions import DataNotFoundError, PromptParsingError


class TestApiEndpoints:
    @pytest.fixture
    def client(self):
        # Use the original app but override dependencies
        from app.api.dependencies import get_backtest_engine, get_nlu_service

        # Create proper mocks
        self.mock_engine = Mock()
        self.mock_nlu_service = AsyncMock()

        def override_get_backtest_engine():
            return self.mock_engine

        def override_get_nlu_service():
            return self.mock_nlu_service

        # Store original dependencies
        self.original_backtest_dep = app.dependency_overrides.get(get_backtest_engine)
        self.original_nlu_dep = app.dependency_overrides.get(get_nlu_service)

        # Override dependencies
        app.dependency_overrides[get_backtest_engine] = override_get_backtest_engine
        app.dependency_overrides[get_nlu_service] = override_get_nlu_service

        yield TestClient(app)

        # Restore original dependencies
        if self.original_backtest_dep is None:
            app.dependency_overrides.pop(get_backtest_engine, None)
        else:
            app.dependency_overrides[get_backtest_engine] = self.original_backtest_dep

        if self.original_nlu_dep is None:
            app.dependency_overrides.pop(get_nlu_service, None)
        else:
            app.dependency_overrides[get_nlu_service] = self.original_nlu_dep

    @pytest.fixture
    def sample_backtest_request(self):
        return {
            "calendar_rules": {"rule_type": "Quarterly", "initial_date": "2024-01-01"},
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 5,
                "data_field": "market_capitalization",
            },
            "weighting_scheme": {"weighting_type": "Equal"},
        }

    @pytest.fixture
    def sample_backtest_response(self):
        return {
            "execution_time": 1.234,
            "weights": {
                "2024-03-31": {"AAPL": 0.5, "MSFT": 0.5},
                "2024-06-30": {"GOOG": 0.33, "AMZN": 0.33, "TSLA": 0.34},
            },
            "metadata": {
                "execution_time": 1.234,
                "rebalance_dates_processed": 2,
                "total_rebalance_dates": 4,
                "average_assets_per_rebalance": 2.5,
                "strategy": {
                    "calendar": "Quarterly",
                    "filter": "TopN",
                    "weighting": "Equal",
                },
            },
            "warnings": [],
        }

    def create_mock_performance_metrics(
        self, execution_time=1.234, weights_count=2, total_dates=4
    ):
        """Create a proper PerformanceMetrics object for mocking."""
        weights_dict = {
            f"2024-03-{i:02d}": {"AAPL": 0.5, "MSFT": 0.5}
            for i in range(1, weights_count + 1)
        }

        return PerformanceMetrics.create(
            execution_time=execution_time,
            weights=weights_dict,
            total_dates=total_dates,
            strategy=StrategySummary(
                calendar="Quarterly", filter="TopN", weighting="Equal"
            ),
        )

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "env" in data

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["message"] == "BITA Backtest API"

    def test_structured_backtest_success(
        self, client, sample_backtest_request, sample_backtest_response
    ):
        """Test successful structured backtest endpoint."""
        # Create proper PerformanceMetrics object
        performance_metrics = self.create_mock_performance_metrics()

        # Mock the backtest engine
        self.mock_engine.run.return_value = (
            sample_backtest_response["weights"],
            performance_metrics,
            sample_backtest_response["warnings"],
        )

        response = client.post("/api/v1/backtest", json=sample_backtest_request)

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "execution_time" in data
        assert "weights" in data
        assert "metadata" in data
        assert "warnings" in data

        # For execution time, just check it's a positive number since we're mocking
        assert data["execution_time"] > 0
        assert len(data["weights"]) == 2
        assert "AAPL" in data["weights"]["2024-03-31"]

        # Verify engine was called with correct request
        self.mock_engine.run.assert_called_once()

    def test_structured_backtest_validation_error(self, client):
        """Test structured backtest with invalid request data."""
        invalid_request = {
            "calendar_rules": {
                "rule_type": "InvalidType",
                "initial_date": "2024-01-01",
            },
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 5,
                "data_field": "market_capitalization",
            },
            "weighting_scheme": {"weighting_type": "Equal"},
        }

        response = client.post("/api/v1/backtest", json=invalid_request)

        assert response.status_code == 422  # Validation error

    def test_structured_backtest_data_not_found(self, client, sample_backtest_request):
        """Test structured backtest when data is not found."""
        self.mock_engine.run.side_effect = DataNotFoundError("Data file not found")

        response = client.post("/api/v1/backtest", json=sample_backtest_request)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Data file not found" in data["detail"]

    def test_structured_backtest_generic_error(self, client, sample_backtest_request):
        """Test structured backtest with generic error."""
        self.mock_engine.run.side_effect = Exception("Unexpected error")

        response = client.post("/api/v1/backtest", json=sample_backtest_request)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Unexpected error" in data["detail"]

    @patch("app.services.nlu_service.get_llm_client")
    def test_prompt_backtest_success(
        self, mock_llm_client, client, sample_backtest_response
    ):
        """Test successful prompt-based backtest endpoint."""
        # Mock LLM client to avoid actual API calls
        mock_llm_instance = AsyncMock()
        mock_llm_instance.generate_json.return_value = {
            "calendar_rules": {"rule_type": "Quarterly", "initial_date": "2023-01-01"},
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 10,
                "data_field": "market_capitalization",
            },
            "weighting_scheme": {"weighting_type": "Equal"},
        }
        mock_llm_client.return_value = mock_llm_instance

        # Mock NLU service response
        self.mock_nlu_service.parse_prompt.return_value = BacktestRequest(
            calendar_rules=CalendarRules(
                rule_type="Quarterly", initial_date=date(2023, 1, 1)
            ),
            portfolio_creation=PortfolioCreation(
                filter_type="TopN", n=10, data_field="market_capitalization"
            ),
            weighting_scheme=WeightingScheme(weighting_type="Equal"),
        )

        # Create proper PerformanceMetrics object
        performance_metrics = self.create_mock_performance_metrics()

        # Mock backtest engine
        self.mock_engine.run.return_value = (
            sample_backtest_response["weights"],
            performance_metrics,
            sample_backtest_response["warnings"],
        )

        prompt_payload = {
            "prompt": "Run a backtest starting from 2023-01-01 with top 10 securities by market cap"
        }

        response = client.post("/api/v1/backtest-prompt", json=prompt_payload)

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "execution_time" in data
        assert "weights" in data
        assert "metadata" in data
        assert "warnings" in data

        # Verify NLU service was called
        self.mock_nlu_service.parse_prompt.assert_called_once_with(
            prompt_payload["prompt"]
        )

        # Verify engine was called
        self.mock_engine.run.assert_called_once()

    @patch("app.services.nlu_service.get_llm_client")
    def test_prompt_backtest_nlu_parsing_error(self, mock_llm_client, client):
        """Test prompt backtest when NLU parsing fails."""
        # Mock LLM client to avoid actual API calls
        mock_llm_instance = AsyncMock()
        mock_llm_instance.generate_json.return_value = {
            "calendar_rules": {"rule_type": "Quarterly", "initial_date": "2023-01-01"},
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 10,
                "data_field": "market_capitalization",
            },
            "weighting_scheme": {"weighting_type": "Equal"},
        }
        mock_llm_client.return_value = mock_llm_instance

        self.mock_nlu_service.parse_prompt.side_effect = PromptParsingError(
            "Failed to parse prompt"
        )

        prompt_payload = {"prompt": "invalid prompt that cannot be parsed"}

        response = client.post("/api/v1/backtest-prompt", json=prompt_payload)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Failed to parse prompt" in data["detail"]

    @patch("app.services.nlu_service.get_llm_client")
    def test_prompt_backtest_empty_prompt(self, mock_llm_client, client):
        """Test prompt backtest with empty prompt."""
        # Mock LLM client to avoid actual API calls
        mock_llm_instance = AsyncMock()
        mock_llm_instance.generate_json.return_value = {
            "calendar_rules": {"rule_type": "Quarterly", "initial_date": "2023-01-01"},
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 10,
                "data_field": "market_capitalization",
            },
            "weighting_scheme": {"weighting_type": "Equal"},
        }
        mock_llm_client.return_value = mock_llm_instance

        self.mock_nlu_service.parse_prompt.side_effect = PromptParsingError(
            "Prompt must be a non-empty string"
        )

        prompt_payload = {"prompt": ""}

        response = client.post("/api/v1/backtest-prompt", json=prompt_payload)

        # Should get 400 from our custom validation
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Prompt must be a non-empty string" in data["detail"]

    def test_prompt_backtest_missing_prompt(self, client):
        """Test prompt backtest with missing prompt field."""
        invalid_payload = {"invalid_field": "some value"}

        response = client.post("/api/v1/backtest-prompt", json=invalid_payload)

        assert response.status_code == 422  # Validation error

    @patch("app.services.nlu_service.get_llm_client")
    def test_prompt_backtest_llm_error(self, mock_llm_client, client):
        """Test prompt backtest when LLM service fails."""
        # Mock LLM client to avoid actual API calls
        mock_llm_instance = AsyncMock()
        mock_llm_instance.generate_json.return_value = {
            "calendar_rules": {"rule_type": "Quarterly", "initial_date": "2023-01-01"},
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 10,
                "data_field": "market_capitalization",
            },
            "weighting_scheme": {"weighting_type": "Equal"},
        }
        mock_llm_client.return_value = mock_llm_instance

        self.mock_nlu_service.parse_prompt.side_effect = Exception(
            "LLM service unavailable"
        )

        prompt_payload = {"prompt": "Run a backtest"}

        response = client.post("/api/v1/backtest-prompt", json=prompt_payload)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_structured_backtest_different_scenarios(self, client):
        """Test structured backtest with different valid scenarios."""
        test_scenarios = [
            {
                "name": "small_portfolio",
                "request": {
                    "calendar_rules": {
                        "rule_type": "Quarterly",
                        "initial_date": "2024-01-01",
                    },
                    "portfolio_creation": {
                        "filter_type": "TopN",
                        "n": 3,
                        "data_field": "volume",
                    },
                    "weighting_scheme": {"weighting_type": "Equal"},
                },
            },
            {
                "name": "large_portfolio",
                "request": {
                    "calendar_rules": {
                        "rule_type": "Quarterly",
                        "initial_date": "2023-06-01",
                    },
                    "portfolio_creation": {
                        "filter_type": "TopN",
                        "n": 50,
                        "data_field": "market_capitalization",
                    },
                    "weighting_scheme": {"weighting_type": "Equal"},
                },
            },
            {
                "name": "adtv_field",
                "request": {
                    "calendar_rules": {
                        "rule_type": "Quarterly",
                        "initial_date": "2024-03-01",
                    },
                    "portfolio_creation": {
                        "filter_type": "TopN",
                        "n": 10,
                        "data_field": "adtv_3_month",
                    },
                    "weighting_scheme": {"weighting_type": "Equal"},
                },
            },
        ]

        for scenario in test_scenarios:
            # Create proper PerformanceMetrics object
            performance_metrics = self.create_mock_performance_metrics(
                execution_time=0.5, weights_count=1
            )

            self.mock_engine.run.return_value = (
                {"2024-03-31": {"AAPL": 1.0}},
                performance_metrics,
                [],
            )

            response = client.post("/api/v1/backtest", json=scenario["request"])

            assert response.status_code == 200, f"Scenario {scenario['name']} failed"
            data = response.json()
            # Just check execution time is positive since we are mocking
            assert data["execution_time"] > 0

    @patch("app.services.nlu_service.get_llm_client")
    def test_prompt_backtest_different_prompts(self, mock_llm_client, client):
        """Test prompt backtest with different natural language prompts."""
        test_prompts = [
            {
                "prompt": "Run a backtest starting from 2023-01-01",
                "expected_n": 10,  # Default value
            },
            {
                "prompt": "Backtest with top 50 securities based on market capitalisation",
                "expected_n": 50,
            },
            {
                "prompt": "Run backtest using volume data from 2022-06-01 with top 25 stocks",
                "expected_n": 25,
            },
            {
                "prompt": "Backtest with ADTV starting 2024-03-01 top 15",
                "expected_n": 15,
            },
        ]

        for test_case in test_prompts:
            # Mock LLM client to avoid actual API calls
            mock_llm_instance = AsyncMock()
            mock_llm_instance.generate_json.return_value = {
                "calendar_rules": {
                    "rule_type": "Quarterly",
                    "initial_date": "2023-01-01",
                },
                "portfolio_creation": {
                    "filter_type": "TopN",
                    "n": test_case["expected_n"],
                    "data_field": "market_capitalization",
                },
                "weighting_scheme": {"weighting_type": "Equal"},
            }
            mock_llm_client.return_value = mock_llm_instance

            # Mock NLU service to return a request with the expected n
            self.mock_nlu_service.parse_prompt.return_value = BacktestRequest(
                calendar_rules=CalendarRules(
                    rule_type="Quarterly", initial_date=date(2023, 1, 1)
                ),
                portfolio_creation=PortfolioCreation(
                    filter_type="TopN",
                    n=test_case["expected_n"],
                    data_field="market_capitalization",
                ),
                weighting_scheme=WeightingScheme(weighting_type="Equal"),
            )

            # Create proper PerformanceMetrics object
            performance_metrics = self.create_mock_performance_metrics(
                execution_time=0.5, weights_count=1
            )

            # Mock backtest engine
            self.mock_engine.run.return_value = (
                {"2024-03-31": {"AAPL": 1.0}},
                performance_metrics,
                [],
            )

            response = client.post(
                "/api/v1/backtest-prompt", json={"prompt": test_case["prompt"]}
            )

            assert response.status_code == 200, f"Prompt failed: {test_case['prompt']}"

            # Verify NLU service was called with correct prompt
            self.mock_nlu_service.parse_prompt.assert_called_with(test_case["prompt"])

    def test_invalid_json_structure(self, client):
        """Test with completely invalid JSON structure."""
        invalid_json = {"completely_wrong": "structure", "missing_required": "fields"}

        response = client.post("/api/v1/backtest", json=invalid_json)

        assert response.status_code == 422  # Validation error

    def test_malformed_json(self, client):
        """Test with malformed JSON."""
        malformed_json = "this is not json"

        response = client.post("/api/v1/backtest", data=malformed_json)

        assert response.status_code == 422  # JSON parse error
