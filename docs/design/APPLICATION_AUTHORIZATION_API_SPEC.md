# NuroCore-License Application Authorization API Spec

This document specifies the **application authorization** (token introspection) API: endpoints, request/response formats, and status codes. These endpoints validate a Bearer token and optionally check that the user has access to a named application, with license expiry enforced first (fail-fast).

**Base path:** All auth endpoints are under `/api/v1/auth`. If the service uses a non-empty `BASE_PATH`, the full path is `{BASE_PATH}/api/v1/auth/...` (e.g. `/nurocore/api/v1/auth/introspect`).

**Common behavior:**
- **Token:** Required via `Authorization: Bearer <token>` (and optionally in body for some POST endpoints).
- **Application name:** Optional on some endpoints, required on others. Used to validate user access to that application and to run license expiry check. Case-insensitive.
- **Application name source priority:** `X-Application-Name` header > `X-Nurol-Application-Name` header > query/body.
- **License check:** If an application name is provided, license expiry is checked first; expired license yields `license_expired` and 401.

---

## 1. GET `/auth/introspect` — nginx auth_request

**Purpose:** Lightweight token validation for nginx `auth_request` (and similar reverse proxies).

### Request

| Source   | Name                     | Type   | Required | Description                          |
|----------|--------------------------|--------|----------|--------------------------------------|
| Header   | `Authorization`          | string | Yes      | `Bearer <token>`                     |
| Header   | `X-Application-Name`     | string | No       | Application to validate access for   |
| Header   | `X-Nurol-Application-Name` | string | No     | Same (legacy)                        |
| Query    | `application_name`       | string | No       | Same (deprecated)                    |

### Response

**Success (200 OK)**  
- Body: `{"status": "valid", "user": "<username>"}`  
- Headers: `X-User`, `X-User-ID`, `X-Token-Status`, and optionally `X-Application`

**Failure**  
- 401 Unauthorized: invalid/expired token, missing token, or `license_expired`. Body includes `"status": "<status>"`.  
- 403 Forbidden: valid token but no access (e.g. `access_denied`, `application_mismatch`). Body includes `"status": "<status>"`.  
- 500: Body `{"error": "..."}`.

**Status values (body and/or `X-Token-Status`):**  
`valid` | `invalid_token` | `invalid_token_format` | `access_denied` | `application_mismatch` | `username_mismatch` | `invalid_format` | `forbidden` | `license_expired` | `error`

---

## 2. POST `/auth/introspect` — RFC 7662–style (minimal response)

**Purpose:** Token introspection with minimal response (only `active`).

### Request

| Source   | Name                     | Type   | Required | Description                          |
|----------|--------------------------|--------|----------|--------------------------------------|
| Header   | `Authorization`          | string | Yes      | `Bearer <token>`                     |
| Header   | `X-Application-Name`     | string | No       | Application to validate access for   |
| Header   | `X-Nurol-Application-Name` | string | No     | Same (legacy)                        |
| Body     | (optional)               | JSON   | No       | May include `application_name`       |

Body example: `{"application_name": "myapp"}`.

### Response

**Success (200 OK)**  
- Body: `{"active": true}` (and possibly other fields).  
- Headers may include `X-User`, `X-User-ID`, `X-Token-Status`, `X-Application`.

**Failure**  
- 401: invalid/expired/missing token or license expired. Body includes `"active": false` and may include `"status"`, `"error"`.  
- 403: valid token but no application access. Body includes `"active": false` and status.  
- 500: Body `{"active": false, "error": "..."}`.

---

## 3. GET `/auth/validate` — simple validation

**Purpose:** Simple valid/not-valid check with small JSON payload.

### Request

| Source   | Name                     | Type   | Required | Description                          |
|----------|--------------------------|--------|----------|--------------------------------------|
| Header   | `Authorization`          | string | Yes      | `Bearer <token>`                     |
| Header   | `X-Application-Name`     | string | No       | Application to validate access for   |
| Header   | `X-Nurol-Application-Name` | string | No     | Same (legacy)                        |
| Query    | `application_name`       | string | No       | Same                                 |

### Response

**Success (200 OK)**  
- Body: `{"valid": true, "status": "valid"}`.

**Failure**  
- 401: invalid/expired/missing token or license expired. Body: `{"valid": false, "status": "<status>"}`.  
- 403: valid token but no access. Body: `{"valid": false, "status": "<status>"}`.  
- 500: Body: `{"valid": false, "status": "error", "error": "..."}`.

**Status values:**  
`valid` | `invalid_token` | `access_denied` | `application_mismatch` | `license_expired` | `forbidden` | `error`

---

## 4. POST `/auth/introspect/application` — application-specific introspection

**Purpose:** Application-scoped introspection with detailed JSON response and nginx-oriented headers. **Application name is required** (header or body).

### Request

| Source   | Name                     | Type   | Required | Description                          |
|----------|--------------------------|--------|----------|--------------------------------------|
| Header   | `Authorization`          | string | No*      | `Bearer <token>`; *required if body `token` not set |
| Header   | `X-Application-Name`     | string | No**     | Application name; **required in header or body |
| Header   | `X-Nurol-Application-Name` | string | No**   | Same (legacy)                        |
| Body     | `application_name`      | string | No**     | Application name (fallback)          |
| Body     | `token`                  | string | No       | Token override; if set, used instead of `Authorization` |

Body example:  
`{"application_name": "myapp", "token": "optional-custom-token-override"}`

### Response

**Success (200 OK)**  
- Body:
  ```json
  {
    "valid": true,
    "status": "valid",
    "message": "Token validation successful",
    "user": "<username>",
    "user_id": "<user_id>",
    "application": "<application_name>"
  }
  ```
- Headers: `X-Auth-Status: valid`, `X-User`, `X-User-ID`, `X-Application`.

**Failure**  
- 400: Missing application name. Body: `{"valid": false, "status": "error", "message": "Application name is required"}`.  
- 401: Missing/invalid token or license expired. Body includes `valid: false`, `status`, `message`, `application`. Headers: `X-Auth-Status: unauthorized`, `X-Application`, optional `WWW-Authenticate: Bearer`.  
- 403: Valid token but no access. Body same shape. Headers: `X-Auth-Status: forbidden`, `X-Application`.  
- 500: Body: `{"valid": false, "status": "error", "message": "..."}`. Header: `X-Auth-Status: error`.

**Example error bodies**

- License expired:
  ```json
  {
    "valid": false,
    "status": "license_expired",
    "message": "License for application 'expired_app' is expired or invalid",
    "application": "expired_app"
  }
  ```
- Access denied:
  ```json
  {
    "valid": false,
    "status": "access_denied",
    "message": "Token validation failed",
    "application": "restricted_app"
  }
  ```

**Status values:**  
`valid` | `invalid_token` | `access_denied` | `application_mismatch` | `license_expired` | `forbidden` | `error`

---

## Token types and validation

- **API tokens:** Identifier format `username-applicationname` (e.g. `john.doe-myapp`). Validated against IAM (identifier, key, expiry, user’s application access).  
- **Access tokens (JWT):** OAuth2/OIDC JWTs; application access derived from group membership (e.g. `"<application_name> Users"`).

Validation order: (1) optional license expiry by application name (fail-fast), (2) token validation, (3) user and application access checks.

---

## Summary table

| Endpoint                      | Method | Token source              | Application name        | Typical use              |
|------------------------------|--------|---------------------------|-------------------------|---------------------------|
| `/auth/introspect`           | GET    | Header only               | Header or query         | nginx auth_request        |
| `/auth/introspect`           | POST   | Header (body optional)    | Header or body          | RFC 7662–style            |
| `/auth/validate`             | GET    | Header only               | Header or query         | Simple valid/invalid      |
| `/auth/introspect/application` | POST | Header or body `token`     | Required: header or body | App-scoped, detailed JSON |

All endpoints return JSON and use the status values and HTTP codes described above. For OpenAPI details (including request body schemas), see the service’s `/docs` (Swagger) or `openapi.json`.
