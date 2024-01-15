#!../venv/bin/python3
"""Fetch a LOT of Amazon product IDs and scrape ~130 reviews from each proportionally"""
from __future__ import annotations

import os
import sqlite3
import sys
from functools import partial
from threading import Lock

import crawling as utils

from wordsmyth import rate

lock = Lock()


class LockedSqliteConnection:
    """https://stackoverflow.com/a/41206801"""

    def __init__(self, dburi: str) -> None:
        self.lock = Lock()
        self.connection = sqlite3.connect(dburi, check_same_thread=False)
        self.cursor: sqlite3.Cursor = None  # type: ignore

    def __enter__(self) -> LockedSqliteConnection:
        self.lock.acquire()
        self.cursor = self.connection.cursor()
        return self

    def __exit__(self, typ, value, traceback) -> None:
        self.lock.release()
        self.connection.commit()
        if self.cursor is not None:
            self.cursor.close()
            self.cursor = None  # type: ignore


def process_reviews(
    reviews: utils.threaded_reviews.Item, db: LockedSqliteConnection
) -> None:
    productId = reviews["productId"]
    with lock:
        for review in reviews["items"]:
            if review["reviewText"].strip() == "":
                return
            with db:
                db.cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS {productId}(text, actual, prediction, flags)"
                )

                try:
                    prediction, flags = rate(
                        review["reviewText"]
                        .replace(
                            "                    The media could not be loaded.\n                ",
                            "",
                        )
                        .strip()
                    )
                except Exception:
                    return
                try:
                    db.cursor.execute(
                        f"INSERT INTO {productId} VALUES(?, ?, ?)",
                        (review["reviewText"], review["overall"], prediction),
                    )
                except AttributeError:
                    db.cursor = db.connection.cursor()
                    db.cursor.execute(
                        f"INSERT INTO {productId} VALUES(?, ?, ?)",
                        (review["reviewText"], review["overall"], prediction),
                    )


def main() -> None:
    from loguru import logger

    HEADLESS = True

    db = LockedSqliteConnection(sys.argv[1])

    with utils.BestSellersLinks(HEADLESS) as products:
        logger.info("Collecting product IDs")
        product_ids = list(products.get_bestselling())

    with utils.AmazonScraper(HEADLESS) as prop:
        with utils.ParallelAmazonScraper(HEADLESS) as scrapers:
            logger.info("Logging scrapers in")
            scrapers.login(os.environ["EMAIL"], os.environ["PASSWORD"])
            # scrapers.scrape(product_id, partial(process_reviews, db=db), proportions)
            for product_id in product_ids:
                proportions = prop.get_proportions(product_id)
                logger.info(f"Collecting review proportions for: {product_id}")

                logger.info(f"Scraping: {product_id}")
                scrapers.scrape(product_id, partial(process_reviews, db=db), proportions)  # type: ignore


if __name__ == "__main__":
    main()
