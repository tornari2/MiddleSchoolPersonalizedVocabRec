#!/usr/bin/env python3
"""
Authentication Utilities for AWS Cognito JWT Verification

This module provides utilities for verifying JWT tokens issued by AWS Cognito
and extracting user information for authorization decisions.
"""

import json
import time
import logging
from typing import Dict, Any, Optional, Tuple
import requests
import jwt
from jwt import PyJWKClient
import base64

logger = logging.getLogger(__name__)

class CognitoJWTVerifier:
    """
    Verifies JWT tokens issued by AWS Cognito User Pools.

    Handles token validation, signature verification, and claim extraction
    for secure authentication in serverless applications.
    """

    def __init__(self, user_pool_id: str, region: str = "us-east-1"):
        """
        Initialize the JWT verifier.

        Args:
            user_pool_id: Cognito User Pool ID (e.g., 'us-east-1_XXXXX')
            region: AWS region where the User Pool is located
        """
        self.user_pool_id = user_pool_id
        self.region = region
        self.jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"

        # Cache for JWKS (JSON Web Key Set)
        self._jwks_client = None
        self._last_jwks_fetch = 0
        self._jwks_cache_ttl = 3600  # 1 hour

        logger.info(f"Initialized CognitoJWTVerifier for User Pool: {user_pool_id}")

    def _get_jwks_client(self) -> PyJWKClient:
        """Get or create cached JWKS client."""
        current_time = time.time()

        if (self._jwks_client is None or
            current_time - self._last_jwks_fetch > self._jwks_cache_ttl):
            try:
                self._jwks_client = PyJWKClient(self.jwks_url)
                self._last_jwks_fetch = current_time
                logger.debug("Refreshed JWKS cache")
            except Exception as e:
                logger.error(f"Failed to fetch JWKS: {e}")
                raise

        return self._jwks_client

    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify and decode a JWT token from Cognito.

        Args:
            token: The JWT token string
            token_type: Type of token ("access", "id", or "refresh")

        Returns:
            Dictionary containing decoded token claims

        Raises:
            ValueError: If token is invalid or verification fails
        """
        try:
            # Decode header to get key ID
            header = jwt.get_unverified_header(token)
            kid = header.get('kid')

            if not kid:
                raise ValueError("Token missing 'kid' in header")

            # Get the signing key
            jwks_client = self._get_jwks_client()
            signing_key = jwks_client.get_jwk_by_kid(kid)

            # Verify and decode the token
            decoded_token = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._get_expected_audience(token_type),
                issuer=self._get_expected_issuer(),
                options={
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_nbf": True
                }
            )

            logger.info(f"Successfully verified {token_type} token for user: {decoded_token.get('sub', 'unknown')}")
            return decoded_token

        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidAudienceError:
            raise ValueError("Token audience mismatch")
        except jwt.InvalidIssuerError:
            raise ValueError("Token issuer mismatch")
        except jwt.InvalidSignatureError:
            raise ValueError("Token signature verification failed")
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise ValueError(f"Token verification failed: {str(e)}")

    def _get_expected_audience(self, token_type: str) -> Optional[str]:
        """
        Get expected audience for token type.

        For access tokens, audience is the User Pool Client ID
        For ID tokens, audience is typically the client ID as well
        """
        if token_type == "access":
            # For access tokens, we might not verify audience strictly
            # since they can be used across multiple clients
            return None
        elif token_type == "id":
            # ID tokens should have the client ID as audience
            # In a production app, you'd pass the client ID here
            return None  # Will be validated in application logic
        return None

    def _get_expected_issuer(self) -> str:
        """Get expected issuer for Cognito tokens."""
        return f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"

    def extract_user_info(self, id_token: str) -> Dict[str, Any]:
        """
        Extract user information from a verified ID token.

        Args:
            id_token: Verified ID token

        Returns:
            Dictionary with user information
        """
        try:
            decoded = self.verify_token(id_token, token_type="id")

            user_info = {
                "user_id": decoded.get("sub"),
                "username": decoded.get("cognito:username"),
                "email": decoded.get("email"),
                "email_verified": decoded.get("email_verified", False),
                "given_name": decoded.get("given_name"),
                "family_name": decoded.get("family_name"),
                "groups": decoded.get("cognito:groups", []),
                "token_use": decoded.get("token_use"),
                "auth_time": decoded.get("auth_time"),
                "iat": decoded.get("iat"),
                "exp": decoded.get("exp")
            }

            return user_info

        except Exception as e:
            logger.error(f"Failed to extract user info: {e}")
            raise

    def validate_request_auth(self, auth_header: str) -> Dict[str, Any]:
        """
        Validate authentication from an HTTP Authorization header.

        Args:
            auth_header: HTTP Authorization header (e.g., "Bearer <token>")

        Returns:
            Dictionary with authentication result and user info

        Raises:
            ValueError: If authentication fails
        """
        if not auth_header or not auth_header.startswith("Bearer "):
            raise ValueError("Missing or invalid Authorization header")

        token = auth_header.replace("Bearer ", "").strip()

        try:
            # Try to decode without verification first to determine token type
            unverified_header = jwt.get_unverified_header(token)
            token_use = unverified_header.get("token_use")

            if token_use == "id":
                # Verify as ID token and extract user info
                user_info = self.extract_user_info(token)
                return {
                    "authenticated": True,
                    "user_info": user_info,
                    "token_type": "id"
                }
            elif token_use == "access":
                # Verify as access token
                access_claims = self.verify_token(token, token_type="access")
                return {
                    "authenticated": True,
                    "user_info": {
                        "user_id": access_claims.get("sub"),
                        "username": access_claims.get("username"),
                        "scope": access_claims.get("scope", []),
                        "groups": access_claims.get("cognito:groups", [])
                    },
                    "token_type": "access"
                }
            else:
                raise ValueError(f"Unknown token type: {token_use}")

        except Exception as e:
            logger.warning(f"Authentication failed: {e}")
            return {
                "authenticated": False,
                "error": str(e)
            }

def create_api_gateway_authorizer(user_pool_id: str, region: str = "us-east-1"):
    """
    Create an API Gateway Lambda authorizer function.

    This function can be used as an AWS Lambda authorizer for API Gateway
    to validate JWT tokens on incoming requests.

    Args:
        user_pool_id: Cognito User Pool ID
        region: AWS region

    Returns:
        Lambda authorizer response
    """
    verifier = CognitoJWTVerifier(user_pool_id, region)

    def authorize(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        API Gateway Lambda authorizer function.

        Args:
            event: API Gateway authorizer event
            context: Lambda context

        Returns:
            IAM policy document for authorization
        """
        try:
            # Extract token from Authorization header
            auth_header = event.get('authorizationToken', '')
            if not auth_header.startswith('Bearer '):
                raise ValueError("Invalid authorization header")

            token = auth_header.replace('Bearer ', '')

            # Verify token
            claims = verifier.verify_token(token, token_type="access")

            # Create policy document
            policy = {
                "principalId": claims.get('sub', 'unknown'),
                "policyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": "execute-api:Invoke",
                            "Effect": "Allow",
                            "Resource": event.get('methodArn', '*')
                        }
                    ]
                },
                "context": {
                    "user_id": claims.get('sub'),
                    "username": claims.get('username'),
                    "groups": claims.get('cognito:groups', []),
                    "scope": claims.get('scope', [])
                }
            }

            return policy

        except Exception as e:
            logger.error(f"Authorization failed: {e}")

            # Return deny policy
            return {
                "principalId": "unauthorized",
                "policyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": "execute-api:Invoke",
                            "Effect": "Deny",
                            "Resource": event.get('methodArn', '*')
                        }
                    ]
                }
            }

    return authorize

# Test functions for development
def test_jwt_verification():
    """Test JWT verification with sample tokens."""
    print("🧪 Testing JWT Verification")
    print("=" * 50)

    # Initialize verifier with actual User Pool ID
    verifier = CognitoJWTVerifier("us-east-1_4l091bzTD", "us-east-1")

    print("✅ JWT Verifier initialized")
    print("📝 Note: Actual token testing requires valid tokens from Cognito")
    print("🔧 In production, tokens would be obtained through Cognito authentication flow")

    # Test with invalid token
    try:
        verifier.verify_token("invalid.jwt.token")
        print("❌ Should have failed with invalid token")
    except ValueError:
        print("✅ Correctly rejected invalid token")

    print("✅ JWT verification framework ready")

def main():
    """Test the authentication utilities."""
    print("🔐 COGNITO JWT VERIFICATION UTILITIES")
    print("=" * 50)

    test_jwt_verification()

    print("\n✅ Authentication utilities ready for integration")
    print("📚 Usage:")
    print("   from auth_utils import CognitoJWTVerifier")
    print("   verifier = CognitoJWTVerifier('us-east-1_XXXXX')")
    print("   claims = verifier.verify_token(token)")

if __name__ == "__main__":
    main()
