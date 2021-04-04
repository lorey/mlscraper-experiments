import logging
import typing
from itertools import product

from more_itertools import flatten

from mlscraper.util import Matcher, Page, Sample, Selector


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
    logging.info(f"generating matchers for samples {samples}")

    pages = {s.page for s in samples}
    # make a list containing sets of nodes for each possible combination of matches
    # -> enables fast searching and set ensures order
    matches_per_sample = [s.get_matches() for s in samples]
    match_combinations = list(map(set, product(*matches_per_sample)))
    node_combinations = [{m.node for m in matches} for matches in match_combinations]

    for sample in samples:
        for match in sample.get_matches():
            for css_sel in match.node.generate_path_selectors():
                logging.info(f"testing selector: {css_sel}")
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
                            f"{css_sel} would need different extractors, ignoring: {match_extractors}"
                        )
