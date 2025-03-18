# Contributing to Reddit AI Trends

Thank you for your interest in contributing to the Reddit AI Trends project! This document provides guidelines and instructions for contributing to our project. By participating, you are expected to uphold our code of conduct and follow these guidelines.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contribution Workflow](#contribution-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)
- [Feature Requests](#feature-requests)
- [Pull Requests](#pull-requests)
- [Community](#community)

## Code of Conduct

Our project is committed to providing a welcoming and inclusive experience for everyone. We expect all participants to adhere to the following principles:

- Be respectful and considerate toward others
- Exercise empathy and kindness
- Provide constructive feedback
- Focus on the best possible outcome for the community
- Respect different viewpoints and experiences

## Getting Started

Before contributing, please ensure you have:

1. Read this contributing guide completely
2. Familiarized yourself with the project by reading the [README.md](README.md)
3. Set up your development environment as described below

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Docker and Docker Compose (optional, for containerized development)
- MongoDB (or use the Docker setup)

### Local Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/reddit-ai-trends.git
   cd reddit-ai-trends
   ```

3. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create a `.env` file from the template:
   ```bash
   cp .env.example .env
   ```

6. Edit the `.env` file with your API keys and configuration options

### Using Docker

Alternatively, you can use Docker:

```bash
docker-compose up -d
```

## Contribution Workflow

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-you-are-fixing
   ```

2. Make your changes with clear, descriptive commits:
   ```bash
   git commit -m "Add feature: detailed description of changes"
   ```

3. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Submit a pull request to the main repository

## Coding Standards

We follow standard Python best practices:

- Follow [PEP 8](https://pep8.org/) for code style
- Use meaningful variable and function names
- Write docstrings for all functions, classes, and modules
- Keep functions focused and small
- Add type hints where appropriate
- Use consistent formatting (consider using tools like `black` and `isort`)

### Code Structure

- Place new modules in the appropriate directories:
  - `services/` for service modules
  - `utils/` for utility functions
  - `database/` for database-related code

## Testing

We encourage test-driven development:

- Write tests for all new functionality
- Update tests when changing existing functionality
- Run the test suite before submitting a pull request:
  ```bash
  python -m unittest discover
  ```

## Documentation

Good documentation is crucial for our project:

- Update documentation when changing functionality
- Document all configuration options
- Provide examples for complex features
- Use clear Markdown formatting

## Issue Reporting

When reporting issues:

1. Check if the issue already exists
2. Use a clear and descriptive title
3. Include detailed steps to reproduce the issue
4. Describe the expected behavior
5. Include screenshots if relevant
6. Mention your environment (OS, Python version, etc.)

## Feature Requests

When suggesting features:

1. Check if the feature has already been suggested
2. Explain how the feature would benefit the project
3. Provide examples of how the feature would work
4. Consider implementation details if possible

## Pull Requests

When submitting pull requests:

1. Ensure your PR addresses an existing issue or feature request
2. Follow the [Contribution Workflow](#contribution-workflow)
3. Include tests for your changes
4. Update documentation as needed
5. Describe your changes in detail in the PR description
6. Link to related issues using keywords like "Fixes #123" or "Relates to #456"

### PR Review Process

1. At least one maintainer must review and approve your PR
2. Address any feedback or requested changes
3. Once approved, a maintainer will merge your PR

## Community

We value community contributions and aim to foster a positive environment:

- Join discussions in issues and pull requests
- Help others with their questions
- Share ideas for improving the project
- Be respectful of others' time and contributions

## Areas We Need Help With

We particularly welcome contributions in these areas:

- **Data Analysis**: Improving trend detection algorithms
- **Visualization**: Adding charts and graphs to reports
- **Multilingual Support**: Enhancing translation quality
- **Performance Optimization**: Making the system more efficient
- **Documentation**: Improving guides and examples
- **Testing**: Expanding test coverage

---

Thank you for taking the time to contribute to our project! Your efforts help make Reddit AI Trends better for everyone.
