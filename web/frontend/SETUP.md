# Web Frontend Setup

This is the web frontend for the Card Sorter system, built with React, TypeScript, and Vite.

## Initial Setup

```bash
# Install dependencies
npm install

# Generate API client from backend OpenAPI spec
npm run generate-client
```

## Development

```bash
# Start development server (with hot reload)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## API Client Generation

The TypeScript API client is automatically generated from the backend's OpenAPI specification:

```bash
npm run generate-client
```

This reads the OpenAPI spec from `../../backend/gen/openapiv2/openapi.swagger.json` and generates a type-safe client in `src/generated/api/`.

**When to regenerate:**
- After updating backend protobuf definitions
- After backend API changes
- When setting up the project for the first time

The generated code is gitignored and should be regenerated locally by each developer.

## Configuration

Create a `.env` file in this directory:

```env
VITE_BACKEND_URL=http://localhost:8080/api
```

## Using the API Client

```typescript
import { configureApiClient, setApiToken } from './lib/api';
import { LibraryServiceService } from './generated/api';

// Configure on app startup
configureApiClient('http://localhost:8080/api');

// Use the services
const libraries = await LibraryServiceService.libraryServiceGetLibraries();

// Update token after login
setApiToken(jwtToken);
```

See `src/lib/example-usage.ts` for more examples.

## Project Structure

```
src/
├── generated/          # Generated API client (gitignored)
│   └── api/
│       ├── services/   # API service classes
│       ├── models/     # TypeScript types
│       └── core/       # Client configuration
├── lib/                # Utility libraries
│   ├── api.ts          # API client configuration
│   └── example-usage.ts # Usage examples
├── assets/             # Static assets
├── App.tsx             # Main app component
└── main.tsx            # Entry point
```

## Dependencies

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Axios** - HTTP client (used by generated API client)
- **React Router** - Routing
- **TanStack Query** - Data fetching and caching
