## ADDED Requirements

### Requirement: OpenAPI Documentation
The backend API SHALL provide comprehensive OpenAPI/Swagger documentation with detailed descriptions for all endpoints, request/response schemas, and examples.

#### Scenario: Developer views API documentation
- **WHEN** developer accesses `/api/docs` (Swagger UI)
- **THEN** all endpoints display descriptions, parameter details, and example values

#### Scenario: Schema documentation
- **WHEN** developer inspects request/response schemas
- **THEN** all fields have descriptions and example values where applicable

### Requirement: TypeScript API Client Generation
The frontend SHALL use auto-generated TypeScript API client from the backend OpenAPI specification.

#### Scenario: Generate API client
- **WHEN** developer runs `pnpm generate:api`
- **THEN** typed API client is generated in `src/api/generated/`

#### Scenario: Type-safe API calls
- **WHEN** frontend code imports from generated client
- **THEN** all request parameters and response types are fully typed
