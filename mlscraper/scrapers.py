class Scraper:
    samples = None

    def __init__(self):
        self.samples = []

    @staticmethod
    def build(page_to_item: dict):
        first_item = list(page_to_item.values())[0]
        scraper = Scraper.for_item(first_item)

        # go through samples one by one
        for page, item in page_to_item.items():
            # - sample exists: extend
            # - sample unknown: create (and set optional)
            scraper.add_sample(page, item)
        return scraper

    @staticmethod
    def for_item(item):
        if isinstance(item, str):
            return ValueScraper()
        elif isinstance(item, list):
            return ListScraper()
        elif isinstance(item, dict):
            return DictScraper()
        else:
            raise RuntimeError(f"unsupported type: {type(item)}")

    def add_sample(self, page, item):
        self.samples.append((page, item))


class DictScraper(Scraper):
    scraper_per_key = None

    def __init__(self):
        super().__init__()
        self.scraper_per_key = {}

    def add_sample(self, page, item):
        assert isinstance(item, dict)
        super().add_sample(page, item)

        for key in item.keys():
            if key not in self.scraper_per_key:
                self.scraper_per_key[key] = Scraper.for_item(item[key])
            self.scraper_per_key[key].add_sample(page, item[key])

    def __repr__(self):
        return f"<DictScraper {self.scraper_per_key=}, {self.samples=}>"


class ListScraper(Scraper):
    scraper = None

    def __init__(self):
        super().__init__()
        self.scraper = None
        self.samples = []

    def add_sample(self, page, item):
        assert isinstance(item, list)
        assert len(item) > 0, "empty list unsupported"
        super().add_sample(page, item)
        self.samples.append(item)

        if not self.scraper:
            self.scraper = Scraper.for_item(item[0])
            if isinstance(self.scraper, ListScraper):
                raise RuntimeError("list in list not allowed")

        for item_inside in item:
            self.scraper.add_sample(page, item_inside)

    def __repr__(self):
        return f"<ListScraper {self.scraper=}, {self.samples=}>"


class ValueScraper(Scraper):
    extractor = None
    selector = None

    def __init__(self):
        super().__init__()
        self.samples = []

    def add_sample(self, page, item):
        assert isinstance(item, str), f"str expected, {type(item)} provided: {item}"
        super().add_sample(page, item)

    def train(self):
        # find items on each page
        # -> return tuple of item and extractor
        # -> choose best extractor

        # train classifier that finds items
        # -> select (subset) items from DOM as False, and found items as True
        # -> generate properties of nodes

        # store found classifier as selector
        pass

    def __repr__(self):
        return f"<ValueScraper {self.samples=}>"
