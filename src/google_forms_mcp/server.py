"""Google Forms MCP Server — Main entry point.

This is the FastMCP server that registers all tools, resources, and prompts,
wires up services via dependency injection, and starts the transport.
"""

from __future__ import annotations

from fastmcp import FastMCP
from googleapiclient.discovery import build

from google_forms_mcp.auth.credential_manager import CredentialManager
from google_forms_mcp.clients.drive_client import DriveClient
from google_forms_mcp.clients.forms_client import FormsClient
from google_forms_mcp.clients.sheets_client import SheetsClient
from google_forms_mcp.config import Settings, TransportMode, get_settings
from google_forms_mcp.infrastructure.logging import get_logger, setup_logging
from google_forms_mcp.infrastructure.rate_limiter import create_default_rate_limiter
from google_forms_mcp.prompts.planning import register_prompts
from google_forms_mcp.resources.forms import register_resources
from google_forms_mcp.services.drive_service import DriveService
from google_forms_mcp.services.forms_service import FormsService
from google_forms_mcp.services.sheets_service import SheetsService
from google_forms_mcp.tools.drive.tools import register_drive_tools
from google_forms_mcp.tools.forms.tools import register_form_tools
from google_forms_mcp.tools.planning.tools import register_planning_tools
from google_forms_mcp.tools.sheets.tools import register_sheets_tools

logger = get_logger("server")


def create_server(settings: Settings | None = None) -> FastMCP:
    """Create and configure the MCP server with all tools and services.

    This is the composition root. All dependency injection happens here.

    Args:
        settings: Application settings. Auto-loaded from env if not provided.

    Returns:
        Configured FastMCP server instance, ready to run.
    """
    if settings is None:
        settings = get_settings()

    # Setup logging
    setup_logging(settings.google_forms_mcp_log_level.value)
    logger.info("Initializing Google Forms MCP Server v0.2.0")

    # Create the MCP server
    mcp = FastMCP(
        name="Google Forms MCP",
        instructions=(
            "This MCP server provides tools to automate Google Forms, Drive, and Sheets. "
            "You can create forms, add questions (all 11 types), manage sections, "
            "configure quiz settings, publish forms, read responses, export data, "
            "manage Drive files/folders, share with permissions, and work with spreadsheets. "
            "\n\n"
            "AI AGENT WORKFLOW:\n"
            "This server includes prompts (e.g. `plan_form`) to help you act as an autonomous "
            "Google Forms agent. When tasked with creating a form, always start by analyzing intent, "
            "asking interactive follow-up questions for missing info, and generating an execution plan "
            "using `validate_execution_plan` before orchestrating tools.\n\n"
            "IMPORTANT NOTES:\n"
            "- Forms created via the API are published automatically by default.\n"
            "- Theme customization (colors, fonts, header images) is NOT supported by the Google Forms API.\n"
            "- Response deletion is NOT supported by the API.\n"
            "- To delete a form, use delete_form (which uses Drive API).\n"
            "- To duplicate a form, use duplicate_form (which uses Drive API).\n"
        ),
    )

    # Create infrastructure
    rate_limiter = create_default_rate_limiter()

    # Create auth manager
    cred_manager = CredentialManager(settings)

    # Get credentials for the default profile
    # Note: In a multi-user server, this would be requested per-invocation.
    # For desktop MCP, we use a single default profile.
    creds = cred_manager.get_valid_credentials("default")

    # Create raw googleapiclient resources
    raw_forms = build("forms", "v1", credentials=creds)
    raw_drive = build("drive", "v3", credentials=creds)
    raw_sheets = build("sheets", "v4", credentials=creds)

    # Create robust API clients mapping HTTP errors to domain errors
    forms_client = FormsClient(raw_forms, rate_limiter, settings)
    drive_client = DriveClient(raw_drive, rate_limiter, settings)
    sheets_client = SheetsClient(raw_sheets, rate_limiter, settings)

    # Create services (domain logic)
    forms_service = FormsService(forms_client)
    drive_service = DriveService(drive_client)
    sheets_service = SheetsService(sheets_client)

    # Register all tools and resources
    register_form_tools(mcp, forms_service, drive_service)
    register_drive_tools(mcp, drive_service)
    register_sheets_tools(mcp, sheets_service)
    register_planning_tools(mcp)
    register_resources(mcp, forms_service, drive_service, sheets_service)
    register_prompts(mcp)

    logger.info("Server initialized with all tools, resources, and prompts registered")

    return mcp


def main() -> None:
    """CLI entry point for the MCP server."""
    settings = get_settings()
    mcp = create_server(settings)

    if settings.google_forms_mcp_transport == TransportMode.HTTP:
        logger.info("Starting HTTP transport on port %d", settings.google_forms_mcp_port)
        mcp.run(transport="streamable-http", port=settings.google_forms_mcp_port)
    else:
        logger.info("Starting STDIO transport")
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
