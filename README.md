<img src="./media/new.svg" height=100 align=right>

# Rateboat

Rateboat was made to ease the pains of manual comment analysis among content creators and viewers to find out how good a video is.
Here's it in a more relatable way:

Imagine you are looking for how to use and make APIs, some tutorial like:

<a href="https://www.youtube.com/watch?v=GZvSYJDk-us"><img src="https://i.ytimg.com/vi/GZvSYJDk-us/hq720.jpg" height=150></a>

You aren't really sure what to expect from the tutorial since it's over 2 hours long and covers a slightly specific topic. Sure, reading the first 10 comments may give you a general idea, but it's not necessarily covering all opinions.

With this tool, all the video comments are aggregated, analyzed for sentiment, and displayed in the most simple way - a rating.

Do you want to scavenge all those comments now?

## Status

Rateboat is currently in development and doesn't have a public API or a frontend, but it is stable for local use.

Please read the [`TODO.md`](./TODO.md) specific things that still need to be implemented.

# Usage

## Requirements

- Python 3
- Docker
- Linux/WSL (only platform the app was tested on)

## Getting started

Clone the repository with `--depth=1` because there is a large file in the Git history and it would take way too long to clone without the flag.

```bash
git clone --depth=1 https://github.com/themysticsavages/rateboat
cd rateboat
```

## Running

### Manual data pipelines

Please read [`CLI.md`](./CLI.md) for how to use the data pipelines without much of the Docker infrastructure.

### Web API (experimental)

Please read [`WEB.md`](./WEB.md) for creating a web server and do other operations with the API (requires all infra to be started)

Most of the documentation for the web API is not finished.
