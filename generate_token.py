#!/usr/bin/env python3
"""Helper script to generate a Google OAuth 2.0 Refresh Token using Client ID and Secret."""

import argparse
import json
import os
import sys
from typing import Any

# Try to load dotenv if available so users don't have to export env vars manually
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes required by Google-Forms-MCP
SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


def load_client_config(client_id: str | None, client_secret: str | None, client_secrets_file: str | None) -> dict[str, Any]:
    """Load OAuth client configuration from arguments, env vars, json file, or interactive prompt."""
    if client_secrets_file and os.path.exists(client_secrets_file):
        print(f"Loading client credentials from {client_secrets_file}...")
        with open(client_secrets_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Support both 'installed' (Desktop app) and 'web' (Web application) client types
            if "installed" in data or "web" in data:
                return data
            return {"installed": data}

    cid = client_id or os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    csecret = client_secret or os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()

    if not cid:
        print("Google OAuth Client ID not found in arguments or GOOGLE_CLIENT_ID environment variable.")
        cid = input("Enter your Google OAuth 2.0 Client ID: ").strip()

    if not csecret:
        print("Google OAuth Client Secret not found in arguments or GOOGLE_CLIENT_SECRET environment variable.")
        csecret = input("Enter your Google OAuth 2.0 Client Secret: ").strip()

    if not cid or not csecret:
        print("\n[ERROR] Both Client ID and Client Secret are required to generate a Refresh Token.")
        sys.exit(1)

    return {
        "installed": {
            "client_id": cid,
            "client_secret": csecret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Google OAuth 2.0 Refresh Token Generator for Google-Forms-MCP")
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8080,
        help="Port for local callback server. MUST match 'Authorized redirect URIs' in Google Cloud Console (default: 8080)."
    )
    parser.add_argument(
        "--client-id",
        type=str,
        help="Your Google OAuth 2.0 Client ID (or set GOOGLE_CLIENT_ID env var)."
    )
    parser.add_argument(
        "--client-secret",
        type=str,
        help="Your Google OAuth 2.0 Client Secret (or set GOOGLE_CLIENT_SECRET env var)."
    )
    parser.add_argument(
        "-f", "--file",
        type=str,
        help="Path to downloaded client_secret_*.json file from Google Cloud Console."
    )
    args = parser.parse_args()

    print("===================================================================")
    print("               Google-Forms-MCP Token Generator                    ")
    print("===================================================================")

    client_config = load_client_config(args.client_id, args.client_secret, args.file)
    
    # Extract client id for display
    config_body = client_config.get("installed") or client_config.get("web", {})
    display_client_id = config_body.get("client_id", "Unknown")

    redirect_uri = f"http://localhost:{args.port}/" if args.port != 80 else "http://localhost/"
    if args.port == 0:
        redirect_uri = "http://localhost:<random-port>/"

    print(f"Client ID: {display_client_id[:15]}...{display_client_id[-10:] if len(display_client_id) > 25 else ''}")
    print(f"Using local server port: {args.port}")
    print(f"Expected Redirect URI: {redirect_uri}")
    print("-------------------------------------------------------------------")
    print("IMPORTANT TROUBLESHOOTING GUIDE:")
    print("1. If you get 'Error 400: redirect_uri_mismatch':")
    print("   -> Go to Google Cloud Console (console.cloud.google.com) -> APIs & Services -> Credentials.")
    print("   -> Click your OAuth 2.0 Client ID.")
    print(f"   -> Under 'Authorized redirect URIs', click '+ ADD URI' and enter exact string: {redirect_uri if args.port != 0 else 'http://localhost:8080/'}")
    print("   -> Click SAVE, wait 30-60 seconds for Google's servers to sync, and re-run this script.")
    print("\n2. If you get 'Access blocked: This app's request is invalid':")
    print("   -> In Google Cloud Console, ensure your OAuth Consent Screen has added your email under 'Test users'.")
    print("===================================================================\n")
    print("Launching browser for Google authentication...")
    print("Please select your Google Account, click 'Continue' (or 'Advanced' -> 'Go to app'), and grant all 4 scopes.\n")

    try:
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        creds = flow.run_local_server(port=args.port, prompt="consent", access_type="offline")

        if not creds.refresh_token:
            print("\n[WARNING] Google did not return a refresh token!")
            print("This usually happens if you previously authorized this app without revoking access.")
            print("To force a new refresh token:")
            print("1. Go to https://myaccount.google.com/connections")
            print("2. Remove access for this OAuth app.")
            print("3. Re-run this script.")
            sys.exit(1)

        print("\n===================================================================")
        print("                        AUTHENTICATION SUCCESS!                    ")
        print("===================================================================")
        print(f"\nYour Refresh Token:\n\n{creds.refresh_token}\n")
        print("===================================================================")

        # Prompt or automatically update .env file
        env_choice = input("Would you like to save/update these credentials in your local .env file? (Y/n): ").strip().lower()
        if env_choice in ("y", "yes", ""):
            cid = config_body.get("client_id", "")
            csecret = config_body.get("client_secret", "")
            
            env_lines = []
            if os.path.exists(".env"):
                with open(".env", "r", encoding="utf-8") as f:
                    for line in f:
                        if not any(line.startswith(k) for k in ("GOOGLE_CLIENT_ID=", "GOOGLE_CLIENT_SECRET=", "GOOGLE_REFRESH_TOKEN=")):
                            env_lines.append(line)
            
            with open(".env", "w", encoding="utf-8") as f:
                f.writelines(env_lines)
                f.write(f"GOOGLE_CLIENT_ID={cid}\n")
                f.write(f"GOOGLE_CLIENT_SECRET={csecret}\n")
                f.write(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}\n")
            
            print("✅ Credentials successfully saved to .env!")

    except Exception as e:
        print(f"\n[ERROR] Authentication failed: {e}")
        print("\nTIP: If you saw 'redirect_uri_mismatch', verify the redirect URI")
        print(f"     ({redirect_uri}) is added under 'Authorized redirect URIs' in Google Cloud Console.")
        sys.exit(1)


if __name__ == "__main__":
    main()
