import typing
from itertools import product

from mlscraper.util import Page


class ItemStructureException(Exception):
    pass


class Match:
    """
    Occurrence of a specific sample on a page
    """


class DictMatch(Match):
    match_by_key = None

    def __init__(self, match_by_key):
        self.match_by_key = match_by_key

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.match_by_key=}>"


class ListMatch(Match):
    matches = None

    def __init__(self, matches):
        self.matches = matches

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.matches=}>"


class ValueMatch(Match):
    node = None
    extractor = None

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.node=}, {self.extractor=}>"


class Sample:
    def __init__(self, page: Page, value: typing.Union[str, list, dict]):
        self.page = page
        self.value = value

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.page=}, {self.value=}>"

    def get_matches(self):
        # todo: fix creating new sample objects, maybe by using Item class?

        if isinstance(self.value, str):
            return self.page.find_all(self.value)

        if isinstance(self.value, list):
            matches_by_value = {
                v: Sample(self.page, v).get_matches() for v in self.value
            }

            # generate list of combinations
            match_combis = product(*[matches_by_value[v] for v in self.value])

            # filter combinations that use the same matches twice
            match_combis_unique = filter(
                lambda mc: len(set(mc)) == len(mc), match_combis
            )

            return [ListMatch(list(match_combi)) for match_combi in match_combis_unique]

        if isinstance(self.value, dict):
            matches_by_key = {
                k: Sample(self.page, self.value[k]).get_matches() for k in self.value
            }
            return [
                DictMatch(dict(zip(matches_by_key.keys(), mc)))
                for mc in product(*matches_by_key.values())
            ]

        raise RuntimeError(f"unsupported value: {self.value}")


class TrainingSet:
    """
    Class containing samples for all pages.
    """

    item = None

    def add_sample(self, sample: Sample):
        if not self.item:
            self.item = Item.create_from(sample.value)

        self.item.add_sample(sample)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.item=}>"


class Item:
    """
    The structure to scrape.
    """

    samples = None

    @classmethod
    def create_from(cls, item):
        if isinstance(item, str):
            return ValueItem()
        elif isinstance(item, list):
            return ListItem()
        elif isinstance(item, dict):
            return DictItem()
        else:
            raise ItemStructureException(f"unsupported item: {type(item)}")

    def __init__(self):
        self.samples = []

    def add_sample(self, sample: Sample):
        self.samples.append(sample)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.samples=}>"


class DictItem(Item):
    items_per_key = None

    def __init__(self):
        super().__init__()
        self.items_per_key = {}

    def add_sample(self, sample: Sample):
        if not isinstance(sample.value, dict):
            raise ItemStructureException(f"dict expected, {sample.value} given")

        super().add_sample(sample)

        for key in sample.value.keys():
            if key not in self.items_per_key:
                self.items_per_key[key] = Item.create_from(sample.value[key])

            self.items_per_key[key].add_sample(Sample(sample.page, sample.value[key]))


class ListItem(Item):
    item = None

    def __init__(self):
        super().__init__()
        self.item = None

    def add_sample(self, sample: Sample):
        if not isinstance(sample.value, list):
            raise ItemStructureException(f"list expected, {sample.value} given")

        super().add_sample(sample)

        if not self.item and len(sample.value):
            self.item = Item.create_from(sample.value[0])

        for v in sample.value:
            self.item.add_sample(v)


class ValueItem(Item):
    def add_sample(self, sample: Sample):
        if not isinstance(sample.value, str):
            raise ItemStructureException(f"str expected, {sample.value} given")
        super().add_sample(sample)


def make_training_set(pages, items):
    assert len(pages) == len(items)

    ts = TrainingSet()
    for p, i in zip(pages, items):
        ts.add_sample(Sample(p, i))

    return ts
