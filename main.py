from inyector import build_app


def main() -> None:
    app = build_app(True, 300)
    try:
        app.run()
    finally:
        app.close()


if __name__ == "__main__":
    main()
