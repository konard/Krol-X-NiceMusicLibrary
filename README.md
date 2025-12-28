# NiceMusicLibrary

Personal music library with mood chains and smart recommendations.

## Features

- Upload and organize personal music
- Modern web player
- Playlists and mood chains
- Listening statistics
- Intelligent recommendations

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- PostgreSQL 15+
- Redis
- SQLAlchemy 2.0
- Alembic (migrations)

### Frontend
- Vue.js 3 + TypeScript
- Pinia (state management)
- Tailwind CSS
- Vite

### Infrastructure
- Docker + Docker Compose
- GitHub Actions (CI/CD)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Krol-X/NiceMusicLibrary.git
   cd NiceMusicLibrary
   ```

2. Copy environment file:
   ```bash
   cp .env.example .env
   ```

3. Start the development environment:
   ```bash
   docker-compose up
   ```

4. Access the application:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Running Tests

Backend:
```bash
docker-compose exec backend pytest
```

Frontend:
```bash
docker-compose exec frontend npm test
```

### Database Migrations

Create a new migration:
```bash
docker-compose exec backend alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
docker-compose exec backend alembic upgrade head
```

## Project Structure

```
.
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Configuration
│   │   ├── db/             # Database
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   ├── alembic/            # Database migrations
│   └── tests/              # Backend tests
├── frontend/               # Vue.js frontend
│   ├── src/
│   │   ├── components/     # Vue components
│   │   ├── views/          # Page views
│   │   ├── stores/         # Pinia stores
│   │   ├── services/       # API services
│   │   └── assets/         # Static assets
│   └── public/             # Public files
├── docs/                   # Documentation
└── docker-compose.yml      # Development setup
```

## Development

### Code Style

- Backend: Ruff (linting + formatting)
- Frontend: ESLint + Prettier

### Pre-commit Hooks

Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

### Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linters
4. Submit a pull request

## Documentation

- [Architecture](docs/01-architecture.md)
- [Entities](docs/02-entities.md)
- [API](docs/03-api.md)
- [User Stories](docs/04-user-stories.md)
- [Interface](docs/05-interface.md)
- [Project Plan](docs/06-project-plan.md)

## License

MIT License - see [LICENSE](LICENSE) for details.
