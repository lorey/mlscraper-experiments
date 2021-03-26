import logging
import typing
from itertools import product

from bs4 import Tag
from more_itertools import flatten, powerset

from mlscraper.util import Sample

PARENT_NODE_COUNT_MAX = 2
CSS_CLASS_COMBINATIONS_MAX = 2


class CssRuleSelector:
    def __init__(self, css_rule):
        self.css_rule = css_rule

    def select(self, page):
        return page.select(self.css_rule)[0]

    def select_all(self, page):
        return page.select(self.css_rule)


def make_css_selector_for_samples(samples):
    for css_selector in generate_css_selectors_for_samples(samples):
        return CssRuleSelector(css_selector)
    return None


def generate_css_selectors_for_samples(
    samples: typing.List[Sample],
) -> typing.Generator:
    """
    Generate CSS selectors that match the given samples.
    :param samples:
    :return:
    """
    pages = {s.page for s in samples}
    # make a list containing sets of nodes for each possible combination of matches
    # -> enables fast searching and set ensures order
    nodes_per_sample = [map(lambda m: m.node, s.get_matches()) for s in samples]
    node_combinations = list(map(set, product(*nodes_per_sample)))

    for sample in samples:
        for match in sample.get_matches():
            for css_sel in generate_path_selector(match.node):
                logging.info(css_sel)
                matched_nodes = set(flatten(page.select(css_sel) for page in pages))
                if matched_nodes in node_combinations:
                    yield css_sel


def generate_node_selector(node):
    """
    Generate a selector for the given node.
    :param node:
    :return:
    """

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

    if isinstance(node.parent, Tag) and hasattr(node, "name"):
        children_tags = [c for c in node.parent.children if isinstance(c, Tag)]
        child_index = list(children_tags).index(node) + 1
        yield ":nth-child(%d)" % child_index

        children_of_same_type = [c for c in children_tags if c.name == node.name]
        child_index = children_of_same_type.index(node) + 1
        yield ":nth-of-type(%d)" % child_index


def powerset_max_length(candidates, length):
    return filter(lambda s: len(s) <= length, powerset(candidates))


def generate_path_selector(node):
    """
    Generate a selector for the path to the given node.
    :param node:
    :return:
    """
    if not isinstance(node, Tag):
        error_msg = "Only tags can be selected with CSS, %s given" % type(node)
        raise RuntimeError(error_msg)

    # we have a list of n ancestor notes and n-1 nodes including the last node
    # the last node must get selected always

    # so we will:
    # 1) generate all selectors for current node
    # 2) append possible selectors for the n-1 descendants
    # starting with all node selectors and increasing number of used descendants

    # remove unique parents as they don't improve selection
    # body is unique, html is unique, document is bs4 root element
    parents = [n for n in node.parents if n.name not in ("body", "html", "[document]")]
    # print(parents)

    # loop from i=0 to i=len(parents) as we consider all parents
    parent_node_count_max = min(len(parents), PARENT_NODE_COUNT_MAX)
    for parent_node_count in range(parent_node_count_max + 1):
        logging.info("path of length %d" % parent_node_count)
        for parent_nodes_sampled in powerset_max_length(parents, parent_node_count):
            path_sampled = (node,) + parent_nodes_sampled
            # logging.info(path_sampled)

            # make a list of selector generators for each node in the path
            # todo limit generated selectors -> huge product
            selector_generators_for_each_path_node = [
                generate_node_selector(n) for n in path_sampled
            ]

            # generator that outputs selector paths
            # e.g. (div, .wrapper, .main)
            path_sampled_selectors = product(*selector_generators_for_each_path_node)

            # create an actual css selector for each selector path
            # e.g. .main > .wrapper > .div
            for path_sampled_selector in path_sampled_selectors:
                # if paths are not directly connected, i.e. (1)-(2)-3-(4)
                #  join must be " " and not " > "
                css_selector = " ".join(reversed(path_sampled_selector))
                yield css_selector
