from mlscraper.scrapers import Scraper


def main():
    pages_dict = {
        "https://stackoverflow.com/questions/6377231/avoid-warnings-on-404-during-django-test-runs": [
            {
                "user": "https://stackoverflow.com/users/624900/jterrace",
                "upvotes": "20",
                "when": "2011-06-16 19:45:11Z",
            },
            {
                "user": "https://stackoverflow.com/users/4044167/nico-knoll",
                "upvotes": "16",
                "when": "2017-09-06 15:27:16Z",
            },
            {
                "user": "https://stackoverflow.com/users/1275778/lorey",
                "upvotes": "0",
                "when": "2021-01-06 10:50:04Z",
            },
        ]
    }
    scraper = Scraper.build(pages_dict)
    print(scraper)


if __name__ == "__main__":
    main()
