## MODIFIED Requirements

### Requirement: Project README Documentation
The project README SHALL accurately reflect the current state of the project, including all features, tech stack, and development commands.

#### Scenario: Developer reads README for setup
- **WHEN** a new developer reads the README
- **THEN** they can set up the complete development environment with accurate commands

#### Scenario: Tech stack accuracy
- **WHEN** README describes the tech stack
- **THEN** it matches the actual dependencies (e.g., RabbitMQ for task queue, not Redis)

#### Scenario: API codegen documentation
- **WHEN** developer wants to regenerate TypeScript API client
- **THEN** README provides the correct command (`pnpm generate:api`)
