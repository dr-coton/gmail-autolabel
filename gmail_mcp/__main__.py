import sys


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "auth":
        from gmail_mcp.client import run_oauth_flow

        run_oauth_flow()
        return

    from gmail_mcp.server import run

    run()


if __name__ == "__main__":
    main()
