import requests
from bs4 import BeautifulSoup


class Page:
    """
    One page, i.e. one HTML document.
    """

    def __init__(self, html):
        self.html = html
        self.soup = BeautifulSoup(self.html, "lxml")

    def find_all(self, item):
        # todo implement other find methods
        return [
            Match(node.parent, Extractor()) for node in self.soup.find_all(text=item)
        ]

    def select(self, css_selector):
        return self.soup.select(css_selector)


class Extractor:
    """
    A class to extract text from a node
    """

    def extract(self, node):
        return node.text


class Match:
    """
    An item found on a page.
    """

    extractor = None
    node = None

    def __init__(self, node, extractor):
        self.node = node
        self.extractor = extractor

    def get_value(self):
        return self.extractor.extract(self.node)


class Sample:
    """
    A sample of data found on a page.
    """

    def __init__(self, page: Page, item):
        self.page = page
        self.item = item

    def __repr__(self):
        return f"<Sample {self.page=}, {self.item=}>"

    def get_matches(self):
        return self.page.find_all(self.item)


def samples_from_url_dict(url_to_item):
    """
    Create samples from dict mapping url->item.
    :param url_to_item:
    :return:
    """
    samples = []
    for url, item in url_to_item.items():
        page_html = requests.get(url).content
        samples.append(Sample(Page(page_html), item))
    return samples
