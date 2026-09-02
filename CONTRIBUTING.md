# Contributing to NexusForge

Thank you for your interest in contributing to NexusForge! This document outlines the guidelines for contributing to the project.

## Getting Started

### Prerequisites
- Git installed
- Docker and Docker Compose installed
- Python 3.11+ installed
- Node.js 18+ installed
- npm or Yarn installed

### Setting Up the Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd nexusforge

# Copy the environment file
cp .env.example .env

# Start the development environment
docker compose up -d

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install
```

### Running Tests

```bash
# Run backend tests
cd backend
pytest

# Run frontend tests
cd ../frontend
npm test
```

## Code Standards

### Backend (Python)
- Follow PEP 8 style guide
- Use type hints for all public functions
- Write docstrings for all modules and public functions
- Use meaningful variable names
- Keep functions focused and single-responsibility

### Frontend (TypeScript)
- Use TypeScript strict mode
- Follow the naming conventions (camelCase for variables, PascalCase for components)
- Use functional components with hooks
- Write JSDoc comments for complex functions
- Use meaningful variable names

### Code Review
- All changes must be reviewed by at least one maintainer
- Code should pass all automated tests
- Documentation should be updated for new features
- Breaking changes should be documented

## Pull Request Process

1. **Fork the repository** and create a feature branch
2. **Make your changes** following the code standards
3. **Write tests** for new functionality
4. **Run all tests** to ensure nothing is broken
5. **Update documentation** if needed
6. **Submit a pull request** with a clear description

### Pull Request Template
```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring

## Checklist
- [ ] Code follows the style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
```

## Reporting Issues

### Bug Reports
- Use the issue tracker
- Provide steps to reproduce
- Include expected and actual behavior
- Add relevant logs and screenshots

### Feature Requests
- Describe the feature and use case
- Explain why it's needed
- Suggest potential implementation approach

## Community Guidelines

### Be Respectful
- Treat all contributors with respect
- Accept constructive criticism
- Focus on what is best for the community

### Be Patient
- Maintainers are volunteers
- Responses may take time
- Not all issues will be resolved immediately

### Be Open
- Welcome newcomers
- Answer questions when you can
- Share knowledge and experience

## Recognition

Contributors are recognized in the project's contributor list and through GitHub's contribution graphs.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.