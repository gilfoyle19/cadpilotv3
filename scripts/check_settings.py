from pprint import pprint

from cadpilotv3.config import get_settings


def main() -> None:
    settings = get_settings()
    pprint(settings.model_dump())


if __name__ == "__main__":
    main()