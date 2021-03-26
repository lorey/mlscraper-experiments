from mlscraper.selectors import (
    generate_css_selectors_for_samples,
    make_css_selector_for_samples,
)
from mlscraper.util import Page, Sample


def test_make_css_selectors_for_samples():
    page1_html = '<html><body><p class="test">test</p><p>bla</p></body></html>'
    page1 = Page(page1_html)
    sample1 = Sample(page1, "test")

    page2_html = '<html><body><div></div><p class="test">hallo</p></body></html>'
    page2 = Page(page2_html)
    sample2 = Sample(page2, "hallo")

    samples = [sample1, sample2]
    assert make_css_selector_for_samples(samples).css_rule in ["p.test", ".test"]


def test_generate_css_selectors_for_samples():
    with open("tests/static/so.html") as file:
        page = Page(file.read())
    samples = [Sample(page, ["20", "16", "0"])]
    selector_first = next(generate_css_selectors_for_samples(samples=samples))
    assert selector_first.endswith(".js-vote-count")
