def build_news_parser(subparsers, cmd_news):
    """Stub for missing news subcommand."""
    news_parser = subparsers.add_parser("news", help="Manage news feeds (Stub)")
    news_parser.set_defaults(func=cmd_news)
    return news_parser
