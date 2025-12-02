# Change: Add Swagger Documentation and OpenAPI TypeScript Codegen

## Status: ✅ 已完成

## Why
1. Backend API endpoints lack detailed descriptions, making it harder for frontend developers to understand the API
2. Frontend currently uses manual axios calls; auto-generated typed API client from OpenAPI spec would improve type safety and reduce maintenance burden

## What Changes
- **Backend**: Add detailed OpenAPI/Swagger descriptions to all API endpoints, schemas, and tags
- **Frontend**: Add `openapi-typescript-codegen` to generate typed API client from backend's OpenAPI spec
- **Build Process**: Add npm script to regenerate API client when spec changes

## Impact
- Affected code:
  - `backend/main.py` - Enhanced OpenAPI metadata
  - `backend/app/api/v1/endpoints/*.py` - Add docstrings with operation descriptions
  - `backend/app/schemas/*.py` - Add Field descriptions and examples
  - `frontend/package.json` - Add openapi-typescript-codegen dependency
  - `frontend/src/api/` - New auto-generated API client directory
