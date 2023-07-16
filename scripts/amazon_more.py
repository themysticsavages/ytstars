"""
Product indexer/review downloader
Bulk-request reviews and dump them to a JSON file
"""
from __future__ import annotations
from typing import Any, Generator, Callable, Optional
from itertools import repeat, count, zip_longest
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

from pyvirtualdisplay.display import Display
from streamlit.runtime.scriptrunner.script_run_context import (
    add_script_run_ctx,
    get_script_run_ctx,
)
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By


map_star = {
    1: "one_star",
    2: "two_star",
    3: "three_star",
    4: "four_star",
    5: "five_star",
}


class AmazonScraper:
    def __init__(self, fake_display: bool = True) -> None:
        if fake_display:
            display = Display(visible=False, size=(800, 600))
            display.start()

        with ThreadPoolExecutor() as executor:
            self.browsers: list[Firefox] = list(
                map(
                    lambda fut: fut.result(),
                    as_completed([executor.submit(Firefox) for _ in range(5)]),
                )
            )

    def _login_single(self, browser: Firefox, email: str, password: str) -> None:
        browser.get("https://amazon.com")
        try:
            browser.find_element(By.ID, "nav-link-accountList").click()
            browser.find_element(By.ID, "ap_email").send_keys(email)
            browser.find_element(By.ID, "continue").click()
            browser.find_element(By.ID, "ap_password").send_keys(password)
            browser.find_element(By.ID, "signInSubmit").click()
        except NoSuchElementException:
            self._login_single(browser, email, password)

    def login(self, email: str, password: str) -> None:
        """Log in all browsers to Amazon with an email and password"""
        with ThreadPoolExecutor() as executor:
            executor.map(
                self._login_single,
                self.browsers,
                repeat(email),
                repeat(password),
            )

    @staticmethod
    def select_reviews(content: Any) -> Generator[dict, None, None]:
        """Select reviews from a Amazon page source"""
        for review in content:
            row = review.select_one(".a-row")
            if row is not None:
                rating = int(
                    row.select_one("i[data-hook='review-star-rating']").text.split(".")[
                        0
                    ]
                )
                body = row.select_one("span[data-hook='review-body']").text
                yield {"reviewText": body.strip(), "overall": rating}

    def _scrape_single(
        self,
        browser: Firefox,
        asin: str,
        category: int,
        callback: Callable[[dict], Any],
        limit: Optional[int] = None,
        ctx: Optional[Any] = None,
    ) -> None:
        if ctx:
            add_script_run_ctx(threading.currentThread(), ctx)
        if limit:
            counter = count(0)

        for page in range(1, 11):
            browser.get(
                f"https://www.amazon.com/product-reviews/{asin}/"
                f"?ie=UTF8&reviewerType=all_reviews&pageNumber={page}&filterByStar={map_star[category]}"
            )
            soup = BeautifulSoup(browser.page_source, "html.parser")
            content = soup.select("div[data-hook='review']")
            for item in self.select_reviews(content):
                if next(counter) >= limit:  # type: ignore
                    return
                callback({**item, "productId": asin})
            time.sleep(0.1)

    def scrape(
        self,
        asin: str,
        callback: Callable[[dict], Any],
        proportions: Optional[list[int]] = None,
    ) -> None:
        """Scrape reviews from all star categories on a product page given an ASIN

        - `callback` is a function which consumes results
        - `proportions` is a list of the number of reviews to scrape from each category
        (none by default)
        """
        if not proportions:
            proportions = []
        with ThreadPoolExecutor() as executor:
            for i, browser, prop in zip_longest(
                range(1, 6), self.browsers, proportions
            ):
                ctx = get_script_run_ctx()
                executor.submit(
                    self._scrape_single, browser, asin, i, callback, prop, ctx
                )

    def close(self) -> None:
        """Close all browsers"""
        with ThreadPoolExecutor() as executor:
            for browser in self.browsers:
                executor.submit(browser.quit)
