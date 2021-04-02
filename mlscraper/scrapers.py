import logging
import typing

from mlscraper.selectors import make_matcher_for_samples
from mlscraper.util import Page, Sample


class Scraper:
    samples = None

    def __init__(self):
        self.samples = []

    @staticmethod
    def build(samples: typing.List[Sample]):
        first_item = samples[0].item
        scraper = Scraper.for_item(first_item)

        # go through samples one by one
        for sample in samples:
            # - sample exists: extend
            # - sample unknown: create (and set optional)
            scraper.add_sample(sample)
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

    def add_sample(self, sample):
        self.samples.append(sample)

    def to_dict(self) -> dict:
        raise NotImplementedError()

    def train(self) -> None:
        raise NotImplementedError()

    def scrape(self, page: Page):
        raise NotImplementedError()

    def scrape_many(self, page: Page):
        raise NotImplementedError()


class DictScraper(Scraper):
    scraper_per_key = None

    def __init__(self):
        super().__init__()
        self.scraper_per_key = {}

    def add_sample(self, sample):
        assert isinstance(sample.item, dict)
        super().add_sample(sample)

        for key in sample.item.keys():
            if key not in self.scraper_per_key:
                self.scraper_per_key[key] = Scraper.for_item(sample.item[key])
            self.scraper_per_key[key].add_sample(Sample(sample.page, sample.item[key]))

    def train(self) -> None:
        for scraper in self.scraper_per_key.values():
            scraper.train()
        logging.info(f"trained {self} successfully")

    def scrape(self, page: Page):
        return {k: self.scraper_per_key[k].scrape(page) for k in self.scraper_per_key}

    def __repr__(self):
        return f"<DictScraper {self.scraper_per_key=}, {self.samples=}>"

    def to_dict(self) -> dict:
        return {
            "DictScraper": {
                "scraper_per_key": {
                    k: s.to_dict() for k, s in self.scraper_per_key.items()
                },
                "samples": self.samples,
            }
        }


class ListScraper(Scraper):
    scraper = None

    def __init__(self):
        super().__init__()
        self.scraper = None
        self.samples = []

    def add_sample(self, sample: Sample):
        assert isinstance(sample.item, list)
        assert len(sample.item) > 0, "empty list unsupported"
        super().add_sample(sample)

        if not self.scraper:
            self.scraper = Scraper.for_item(sample.item[0])
            if isinstance(self.scraper, ListScraper):
                raise RuntimeError("list in list not allowed")

        for item_inside in sample.item:
            self.scraper.add_sample(Sample(sample.page, item_inside))

    def train(self) -> None:
        # train the scraper that selects this list's items
        self.scraper.train()

    def scrape(self, page: Page):
        return self.scraper.scrape_many(page)

    def __repr__(self):
        return f"<ListScraper {self.scraper=}, {self.samples=}>"

    def to_dict(self) -> dict:
        return {
            "ListScraper": {"scraper": self.scraper.to_dict(), "samples": self.samples}
        }


class ValueScraper(Scraper):
    matcher = None

    def __init__(self):
        super().__init__()
        self.samples = []

    def add_sample(self, sample: Sample):
        assert isinstance(
            sample.item, str
        ), f"str expected, {type(sample.item)} provided: {sample.item}"
        super().add_sample(sample)

    def train(self):
        self.matcher = make_matcher_for_samples(self.samples)
        logging.info(f"trained {self} sucessfully: {self.matcher=}")

    def scrape(self, page: Page):
        return self.matcher.match_one(page)

    def scrape_many(self, page: Page):
        return self.matcher.match_all(page)

    def __repr__(self):
        return f"<ValueScraper {self.samples=}>"

    def to_dict(self) -> dict:
        return {
            "ValueScraper": {
                "selector": None,
                "extractor": None,
                "samples": self.samples,
            }
        }
