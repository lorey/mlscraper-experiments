import logging

from mlscraper.scrapers import Scraper
from mlscraper.util import samples_from_url_dict


def main():
    pages_dict = {
        "https://stackoverflow.com/questions/6377231/avoid-warnings-on-404-during-django-test-runs": [
            {
                "user": "/users/624900/jterrace",
                "upvotes": "20",
                "when": "2011-06-16 19:45:11Z",
            },
            {
                "user": "/users/4044167/nico-knoll",
                "upvotes": "16",
                "when": "2017-09-06 15:27:16Z",
            },
            {
                "user": "/users/1275778/lorey",
                "upvotes": "0",
                "when": "2021-01-06 10:50:04Z",
            },
        ]
    }
    samples = samples_from_url_dict(pages_dict)
    scraper = Scraper.build(samples)
    scraper.train()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
