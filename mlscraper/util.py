class Page:
    """
    One page, i.e. one HTML document.
    """

    def __init__(self, html):
        self.html = html


class Sample:
    """
    A sample of data found on a page.
    """

    def __init__(self, page: Page, item):
        self.page = page
        self.item = item

    def __repr__(self):
        return f"<Sample {self.page=}, {self.item=}>"


def samples_from_url_dict(url_to_item):
    """
    Create samples from dict mapping url->item.
    :param url_to_item:
    :return:
    """
    samples = []
    for url, item in url_to_item.items():
        page_html = url
        samples.append(Sample(Page(page_html), item))
    return samples
