# Bitacore - Mini Backtest API

## Overview

A high-performance financial backtesting API with NLP capabilities. Built with FastAPI, DuckDB, and SOLID architecture principles.

## Features

- **Structured Backtesting**: JSON-based backtest configuration
- **NLP Integration**: Natural language prompt parsing with multiple LLM providers
- **High Performance**: DuckDB-powered data processing
- **Multi-Storage**: Local filesystem and S3 support
- **Extensible Architecture**: Factory patterns for easy extension

## Quick Start

### Prerequisites

- Python 3.11+
- UV package manager
- OpenAI or Gemini API key (for NLP features)

### Local Development

1. **Clone and setup:**
    ```
    git clone <repository>
    cd bitacore
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

2. **Install dependencies:**
    ```bash
      make install
     ```
   3. **Configure environment:**
   
   ```bash
      cp .env.example .env # Edit .env with your API keys and settings
     ```
   4. **Generate sample data:**
      ```bash
      make generate
        
5. **Run the application:**

    ```bash
       make dev
   
### Docker


### Build and start services
   ```bash
        make build
        make up
        
        View logs
        make logs
        
        ### Stop services
       make down
  ```

## API Endpoints

### Structured Backtest

```
POST /api/v1/backtest
Content-Type: application/json

{
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
```
### Prompt-Based Backtest

```
POST /api/v1/backtest-prompt
Content-Type: application/json

{
"prompt": "Run a backtest starting from 2023-01-01 with top 5 securities by volume"
}
```


### Health Check
```
GET /health
```


## Configuration

### Environment Variables

- LLM_PROVIDER: openai or gemini
- OPENAI_API_KEY: Your OpenAI API key
- GEMINI_API_KEY: Your Gemini API key
- STORAGE_BACKEND: local or s3
- LOCAL_DATA_DIR: Local data directory path
- S3_BUCKET: S3 bucket name (for S3 storage)
- AWS_REGION: AWS region for S3

### Data Format

- Parquet files with the following structure:
    - Wide format: Date index with securities as columns
    - Long format: [date, security, value] columns for DuckDB optimization

## Development

### Testing

   ```bash
        make test # Run tests with coverage
        make lint # Run linter
        make format # Format code
        make type-check # Type checking
  ```

### Adding New Components

**New Calendar Rule:**
- Implement `BaseCalendar` in `app/backtest/calendar/`
- Add to factory in `app/backtest/calendar/factory.py`

**New Filter:**
- Implement `BaseFilter` in `app/backtest/filters/`
- Add to factory in `app/backtest/filters/factory.py`

**New Weighting Scheme:**
- Implement `BaseWeighting` in `app/backtest/weighting/`
- Add to factory in `app/backtest/weighting/factory.py`

## Architecture

The application follows SOLID principles with:
- Dependency Injection: FastAPI dependency system
- Factory Pattern: Extensible component creation
- Strategy Pattern: Interchangeable algorithms
- Repository Pattern: Data access abstraction

## Deployment
### AWS and Terraform Requirements

If you plan to deploy to AWS ECS using Terraform, you will need to install and configure both the AWS Command Line Interface (CLI) and Terraform.

#### 1. Install Terraform

Terraform is used to manage and provision your infrastructure.

* **Linux/macOS:**
    1.  Download the appropriate package from the official HashiCorp website.
    2.  Unzip the package.
    3.  Move the `terraform` executable to a location in your system's `PATH` (e.g., `/usr/local/bin`).
* **macOS (via Homebrew):**
    ```bash
    brew install terraform
    ```
* **Windows (via Chocolatey):**
    ```bash
    choco install terraform
    ```
* **Verification:**
    ```bash
    terraform --version
    ```



[TODO: Image of Terraform workflow diagram]


#### 2. Install AWS CLI

The AWS CLI is required for configuring your machine to interact with your AWS account and for Terraform to execute cloud provisioning.

* **macOS/Linux/Windows:** Follow the official installation instructions for your OS. The recommended method is often using the OS-specific package manager or installer.
    * *For example, using `curl` on Linux/macOS to install v2:*
        ```bash
        curl "[https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip](https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip)" -o "awscliv2.zip"
        unzip awscliv2.zip
        sudo ./aws/install
        ```
* **Verification:**
    ```bash
    aws --version
    ```

#### 3. Configure AWS CLI

After installation, you must configure your access credentials.

1.  **Generate Credentials:** Log into your AWS Management Console, create an IAM user, and generate an Access Key ID and Secret Access Key.

2.  **Configure:** Run the following command and enter your keys, default region (e.g., `us-east-1`), and output format (`json`).

    ```bash
    aws configure
    ```

    *Example Output:*

    ```
    AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
    AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    Default region name [None]: us-east-1
    Default output format [None]: json
    ```

3.  **Verification (Check your identity):**

    ```bash
    aws sts get-caller-identity
    ```
### AWS ECS with Terraform

   ```bash
        cd terraform
        terraform init
        terraform plan
        terraform apply
  ```


## Docker Registry

### Build and push to registry

   ```bash
        docker build -t your-registry/bitacore:latest .
        docker push your-registry/bitacore:latest
  ```

## Performance

- DuckDB Integration: 10-100x faster data processing
- Async Support: Non-blocking NLP operations
- Memory Efficient: Columnar data processing
- Parallel Processing: Multi-threaded execution

## License

MIT License

