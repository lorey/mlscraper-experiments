import logging
import typing
from itertools import combinations, product

import requests
from bs4 import BeautifulSoup, Tag
from more_itertools import powerset

PARENT_NODE_COUNT_MAX = 2
CSS_CLASS_COMBINATIONS_MAX = 2

extractor_instance_map = {}
node_instance_map = {}


def get_text_extractor():
    map_key = ("text",)
    if map_key not in extractor_instance_map:
        extractor_instance_map[map_key] = TextValueExtractor()
    return extractor_instance_map[map_key]


def get_attribute_extractor(attr):
    map_key = ("attr", attr)
    if map_key not in extractor_instance_map:
        extractor_instance_map[map_key] = AttributeValueExtractor(attr)
    return extractor_instance_map[map_key]


def get_node_for_soup(soup):
    if soup not in node_instance_map:
        node_instance_map[soup] = Node(soup)
    return node_instance_map[soup]


class Node:
    soup = None

    def __init__(self, soup):
        self.soup = soup

    def get_text(self):
        return self.soup.text

    text = property(get_text)

    def find_all(self, item):
        return list(self._generate_find_all(item))

    def _generate_find_all(self, item):
        # text
        for soup_node in self.soup.find_all(text=item):
            node = get_node_for_soup(soup_node.parent)
            yield Match(node, get_text_extractor())

        # attributes
        for soup_node in self.soup.find_all():
            for attr in soup_node.attrs:
                if soup_node[attr] == item:
                    node = get_node_for_soup(soup_node)
                    yield Match(node, get_attribute_extractor(attr))

        # todo implement other find methods

    def generate_path_selectors(self):
        """
        Generate a selector for the path to the given node.
        :return:
        """
        if not isinstance(self.soup, Tag):
            error_msg = "Only tags can be selected with CSS, %s given" % type(self.soup)
            raise RuntimeError(error_msg)

        # we have a list of n ancestor notes and n-1 nodes including the last node
        # the last node must get selected always

        # so we will:
        # 1) generate all selectors for current node
        # 2) append possible selectors for the n-1 descendants
        # starting with all node selectors and increasing number of used descendants

        # remove unique parents as they don't improve selection
        # body is unique, html is unique, document is bs4 root element
        parents = [
            n for n in self.soup.parents if n.name not in ("body", "html", "[document]")
        ]
        # print(parents)

        # loop from i=0 to i=len(parents) as we consider all parents
        parent_node_count_max = min(len(parents), PARENT_NODE_COUNT_MAX)
        for parent_node_count in range(parent_node_count_max + 1):
            logging.info(
                "generating path selectors with %d parents" % parent_node_count
            )
            # generate paths with exactly parent_node_count nodes
            for parent_nodes_sampled in combinations(parents, parent_node_count):
                path_sampled = (self.soup,) + parent_nodes_sampled
                # logging.info(path_sampled)

                # make a list of selector generators for each node in the path
                # todo limit generated selectors -> huge product
                selector_generators_for_each_path_node = [
                    generate_node_selector(n) for n in path_sampled
                ]

                # generator that outputs selector paths
                # e.g. (div, .wrapper, .main)
                path_sampled_selectors = product(
                    *selector_generators_for_each_path_node
                )

                # create an actual css selector for each selector path
                # e.g. .main > .wrapper > .div
                for path_sampled_selector in path_sampled_selectors:
                    # if paths are not directly connected, i.e. (1)-(2)-3-(4)
                    #  join must be " " and not " > "
                    css_selector = " ".join(reversed(path_sampled_selector))
                    yield css_selector

    def select(self, css_selector):
        return [get_node_for_soup(n) for n in self.soup.select(css_selector)]

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.soup}>"


class Page(Node):
    """
    One page, i.e. one HTML document.
    """

    def __init__(self, html):
        self.html = html
        soup = BeautifulSoup(self.html, "lxml")
        super().__init__(soup)


class Extractor:
    """
    Class that extracts values from a node.
    """

    def extract(self, node: Node):
        raise NotImplementedError()


class TextValueExtractor(Extractor):
    """
    Class to extract text from a node.
    """

    def extract(self, node: Node):
        return node.soup.text

    def __repr__(self):
        return f"<{self.__class__.__name__}>"


class AttributeValueExtractor(Extractor):
    attr = None

    def __init__(self, attr):
        self.attr = attr

    def extract(self, node: Node):
        if self.attr in node.soup.attrs:
            return node.soup[self.attr]

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.attr=}>"


class Match:
    """
    An item found on a page.
    """

    extractor = None
    node = None

    def __init__(self, node: Node, extractor: Extractor):
        self.node = node
        self.extractor = extractor

    def get_value(self):
        return self.extractor.extract(self.node)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.extractor=} {self.node=}>"


class Selector:
    """
    Class to select nodes from another node.
    """

    def select_one(self, node: Node) -> Node:
        raise NotImplementedError()

    def select_all(self, node: Node) -> typing.List[Node]:
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

    def match_one(self, node: Node) -> Match:
        selected_node = self.selector.select_one(node)
        return Match(selected_node, self.extractor)

    def match_all(self, node: Node) -> typing.List[Match]:
        selected_nodes = self.selector.select_all(node)
        return [Match(n, self.extractor) for n in selected_nodes]

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.selector=} {self.extractor=}>"


class DictExtractor(Extractor):
    def __init__(self, matcher_by_key: typing.Dict[str, Matcher]):
        self.matcher_by_key = matcher_by_key

    def extract(self, node: Node):
        return {
            key: matcher.match_one(node) for key, matcher in self.matcher_by_key.items()
        }


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

    def get_matches(self) -> typing.List[Match]:
        if isinstance(self.item, str):
            return self.page.find_all(self.item)

        if isinstance(self.item, dict):
            keys = self.item.keys()
            matches_by_key = {
                k: Sample(self.page, self.item[k]).get_matches() for k in keys
            }
            for key, matches in matches_by_key.items():
                assert len(matches) > 0, f"no match found for {key}"

            # get all possible combinations of matches
            lod = []
            for matches in product(*matches_by_key.values()):
                lod.append(dict(zip(keys, matches)))
            return lod

        raise NotImplementedError(
            f"finding matches only works for trivial samples, not {type(self.item)}: {self.item}"
        )


def samples_from_url_dict(url_to_item):
    """
    Create samples from dict mapping url->item.
    :param url_to_item:
    :return:
    """
    samples = []
    for url, item in url_to_item.items():
        page_html = requests.get(url).content
        page = Page(page_html)
        samples.append(Sample(page, item))
    return samples


def generate_node_selector(node):
    """
    Generate a selector for the given node.
    :param node:
    :return:
    """
    assert isinstance(node, Tag)

    # use id
    tag_id = node.attrs.get("id", None)
    if tag_id:
        yield "#" + tag_id

    # use classes
    css_classes = node.attrs.get("class", [])
    for css_class_combo in powerset_max_length(css_classes, CSS_CLASS_COMBINATIONS_MAX):
        css_clases_str = "".join(
            [".{}".format(css_class) for css_class in css_class_combo]
        )
        css_selector = node.name + css_clases_str
        yield css_selector

    # todo: nth applies to whole selectors
    #  -> should thus be a step after actual selector generation
    if isinstance(node.parent, Tag) and hasattr(node, "name"):
        children_tags = [c for c in node.parent.children if isinstance(c, Tag)]
        child_index = list(children_tags).index(node) + 1
        yield ":nth-child(%d)" % child_index

        children_of_same_type = [c for c in children_tags if c.name == node.name]
        child_index = children_of_same_type.index(node) + 1
        yield ":nth-of-type(%d)" % child_index


def powerset_max_length(candidates, length):
    return filter(lambda s: len(s) <= length, powerset(candidates))


def get_common_ancestor_for_nodes(nodes):
    # todo might require adding node here!
    paths_of_nodes = [list(reversed(list(node.parents))) for node in nodes]
    ancestor = _get_common_ancestor_for_paths(paths_of_nodes)
    return ancestor


def _get_common_ancestor_for_paths(paths):
    """
    Computes the first common ancestor for list of paths.
    :param paths: list of list of nodes from top to bottom
    :return: first common index or RuntimeError
    """
    # go through path one by one
    # while len(set([paths[n][i] for n in range(len(paths))])) == 1:
    ind = None
    for i, nodes in enumerate(zip(*paths)):
        # as long as all nodes are the same
        # -> go deeper
        # else break
        if len(set(nodes)) != 1:
            # return parent of mismatch
            break

        # set after as this remembers the last common index
        ind = i

    # if index is unset, even the first nodes didn't match
    if ind is None:
        raise RuntimeError("No common ancestor")

    # as all nodes are the same, we can just use the first path
    return paths[0][ind]
