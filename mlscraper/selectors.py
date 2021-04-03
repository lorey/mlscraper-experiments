import logging
import typing
from itertools import combinations, product

from bs4 import Tag
from more_itertools import flatten, powerset

from mlscraper.util import Matcher, Page, Sample, Selector

PARENT_NODE_COUNT_MAX = 2
CSS_CLASS_COMBINATIONS_MAX = 2


class CssRuleSelector(Selector):
    def __init__(self, css_rule):
        self.css_rule = css_rule

    def select_one(self, page: Page):
        return page.select(self.css_rule)[0]

    def select_all(self, page):
        return page.select(self.css_rule)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.css_rule=}>"


def make_matcher_for_samples(samples):
    for sample in samples:
        assert sample.get_matches(), f"no matches found for {sample}"

    for matcher in generate_matchers_for_samples(samples):
        return matcher
    return None


def generate_matchers_for_samples(
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
    matches_per_sample = [s.get_matches() for s in samples]
    match_combinations = list(map(set, product(*matches_per_sample)))
    node_combinations = [{m.node for m in matches} for matches in match_combinations]

    for sample in samples:
        for match in sample.get_matches():
            for css_sel in generate_path_selector(match.node):
                logging.debug(f"testing selector: {css_sel}")
                matched_nodes = set(flatten(page.select(css_sel) for page in pages))
                if matched_nodes in node_combinations:
                    logging.info(f"{css_sel} matches one of the possible combinations")
                    i = node_combinations.index(matched_nodes)
                    matches = match_combinations[i]
                    match_extractors = {m.extractor for m in matches}
                    if len(match_extractors) == 1:
                        logging.info(f"{css_sel} matches same extractors")
                        selector = CssRuleSelector(css_sel)
                        extractor = next(iter(match_extractors))
                        yield Matcher(selector, extractor)
                    else:
                        logging.info(
                            f"{css_sel} would need different extractors: {match_extractors}"
                        )


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
        logging.info("generating path selectors with %d parents" % parent_node_count)
        # generate paths with exactly parent_node_count nodes
        for parent_nodes_sampled in combinations(parents, parent_node_count):
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
