from inyector import build_app


def main() -> None:
    app = build_app(use_undetected=True, max_per_volume=300, is_chromium=False)
    try:
        app.run()
    finally:
        app.close()


if __name__ == "__main__":
    main()
