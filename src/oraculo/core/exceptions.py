"""Excepciones especificas del Oraculo. Catalogo unico para toda la aplicacion."""


class OraculoError(Exception):
    """Base para todas las excepciones del Oraculo."""
    code: str = "ORC_GENERIC"


class ProfileError(OraculoError):
    code = "ORC_PROFILE"


class ProfileNotFoundError(ProfileError):
    code = "ORC_PROFILE_NOT_FOUND"


class ProfileValidationError(ProfileError):
    code = "ORC_PROFILE_INVALID"


class ProfileDowngradeError(ProfileError):
    code = "ORC_PROFILE_DOWNGRADE_DENIED"


class ProfileSignatureError(ProfileError):
    code = "ORC_PROFILE_SIG_INVALID"


class CryptoError(OraculoError):
    code = "ORC_CRYPTO"


class AuthError(OraculoError):
    code = "ORC_AUTH"


class TokenExpiredError(AuthError):
    code = "ORC_TOKEN_EXPIRED"


class RateLimitError(OraculoError):
    code = "ORC_RATE_LIMIT"


class IntegrityError(OraculoError):
    code = "ORC_INTEGRITY"


class DegradedModeError(OraculoError):
    code = "ORC_DEGRADED"


class IndexError(OraculoError):
    code = "ORC_INDEX"


class ParserError(OraculoError):
    code = "ORC_PARSER"
