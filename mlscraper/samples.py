class ItemStructureException(Exception):
    pass


class Sample:
    def __init__(self, page, value):
        self.page = page
        self.value = value

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.page=}, {self.value=}>"


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


class Match:
    pass


class DictMatch(Match):
    match_by_key = None


class ListMatch(Match):
    matches = None


class ValueMatch(Match):
    node = None
    extractor = None


def make_training_set(pages, items):
    assert len(pages) == len(items)

    ts = TrainingSet()
    for p, i in zip(pages, items):
        ts.add_sample(Sample(p, i))

    return ts
