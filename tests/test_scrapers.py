from bs4 import BeautifulSoup

from mlscraper.scrapers import ValueScraper, Scraper, ListScraper, DictScraper


def test_value_scraper():
    page1_html = '<html><body><p class="test">test</p><p>bla</p></body></html>'
    page1 = BeautifulSoup(page1_html, "lxml")

    page2_html = '<html><body><div></div><p class="test">hallo</p></body></html>'
    page2 = BeautifulSoup(page2_html, "lxml")

    vs = ValueScraper()
    vs.samples = [(page1, "test"), (page2, "hallo")]


def test_scraper_build():
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
    assert isinstance(scraper, ListScraper)
    print(scraper.samples)
    url = "https://stackoverflow.com/questions/6377231/avoid-warnings-on-404-during-django-test-runs"
    assert scraper.samples[0] == (url, pages_dict[url])

    dict_scraper = scraper.scraper
    assert isinstance(dict_scraper, DictScraper)
    assert list(dict_scraper.scraper_per_key.keys()) == ["user", "upvotes", "when"]
