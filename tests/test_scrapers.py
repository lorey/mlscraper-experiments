from bs4 import BeautifulSoup

from mlscraper.scrapers import ValueScraper


def test_value_scraper():
    page1_html = '<html><body><p class="test">test</p><p>bla</p></body></html>'
    page1 = BeautifulSoup(page1_html, "lxml")

    page2_html = '<html><body><div></div><p class="test">hallo</p></body></html>'
    page2 = BeautifulSoup(page2_html, "lxml")

    vs = ValueScraper()
    vs.samples = [(page1, "test"), (page2, "hallo")]
