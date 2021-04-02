import typing

import requests
from bs4 import BeautifulSoup

extractor_instance_map = {}


def get_text_extractor():
    map_key = ("text",)
    if map_key not in extractor_instance_map:
        extractor_instance_map[map_key] = TextExtractor()
    return extractor_instance_map[map_key]


def get_attribute_extractor(attr):
    map_key = ("attr", attr)
    if map_key not in extractor_instance_map:
        extractor_instance_map[map_key] = AttributeExtractor(attr)
    return extractor_instance_map[map_key]


class Page:
    """
    One page, i.e. one HTML document.
    """

    def __init__(self, html):
        self.html = html
        self.soup = BeautifulSoup(self.html, "lxml")

    def find_all(self, item):
        return list(self._generate_find_all(item))

    def _generate_find_all(self, item):
        # text
        for node in self.soup.find_all(text=item):
            yield Match(node.parent, get_text_extractor())

        # attributes
        for node in self.soup.find_all():
            for attr in node.attrs:
                if node[attr] == item:
                    yield Match(node, get_attribute_extractor(attr))

        # todo implement other find methods

    def select(self, css_selector):
        return self.soup.select(css_selector)


class Extractor:
    """
    Class that extracts values from a node.
    """

    def extract(self, node):
        raise NotImplementedError()


class TextExtractor(Extractor):
    """
    Class to extract text from a node.
    """

    def extract(self, node):
        return node.text


class AttributeExtractor(Extractor):
    attr = None

    def __init__(self, attr):
        self.attr = attr

    def extract(self, node):
        if self.attr in node.attrs:
            return node[self.attr]

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.attr=}>"


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

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.extractor=} {self.node=}>"


class Selector:
    """
    Class to select nodes from a page.
    """

    def select_one(self, page: Page):
        raise NotImplementedError()

    def select_all(self, page: Page):
        raise NotImplementedError()


class Matcher:
    """
    Class that finds/selects nodes and extracts items from these nodes.
    """

    selector = None
    extractor = None

    def __init__(self, selector: Selector, extractor: Extractor):
        self.selector = selector
        self.extractor = extractor

    def match_one(self, page: Page):
        node = self.selector.select_one(page)
        return Match(node, self.extractor)

    def match_all(self, page: Page) -> typing.List[Match]:
        nodes = self.selector.select_all(page)
        return [Match(node, self.extractor) for node in nodes]

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.selector=} {self.extractor=}>"


class Sample:
    """
    A sample of data found on a page.
    """

    page = None
    item = None

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
