import sys


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] == "auth":
        force = any(a in ("--force", "--refresh") for a in args[1:])
        from gmail_autolabel.client import run_oauth_flow

        run_oauth_flow(force=force)
        return

    from gmail_autolabel.server import run

    run()


if __name__ == "__main__":
    main()
