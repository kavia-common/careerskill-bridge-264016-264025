# SkillBridge Backend Auth Notes

## Authorization header contract (REST)
Authenticated endpoints (e.g. `GET /users/me`) expect one of:

- `Authorization: Bearer <JWT>` (preferred)
- `X-Authorization: Bearer <JWT>` (proxy fallback)
- `X-Access-Token: <JWT>` (proxy fallback)

The canonical dependency is `src.api.deps.get_current_user`.

## passlib / bcrypt compatibility
This backend uses:

- `passlib==1.7.4`
- `bcrypt==4.x`

`passlib` 1.7.4 attempts to read the bcrypt version from `bcrypt.__about__.__version__`,
but bcrypt 4.x no longer ships `__about__`. This can cause noisy logs and can break
bcrypt handler initialization in some environments.

To keep behavior stable without changing dependencies, `src.core.security` applies a
small, best-effort shim that adds `bcrypt.__about__.__version__` at import time when missing.
