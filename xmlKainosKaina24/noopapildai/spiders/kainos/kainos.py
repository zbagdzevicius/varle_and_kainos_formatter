import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import os

class MySpider(scrapy.Spider):
    name = 'noopapildai'

    start_urls = [
        'https://www.noopapildai.lt/kategorija/amino-rugstys/']

    def parse(self, response):
        for category in response.css('ul.product-categories li.cat-item a::attr(href)').extract():
            yield response.follow(category, self.follow_products)

    def parse_pagination(self, response):
        for page in response.css('ul.page-numbers.nav-pagination.links.text-center li'):
            if page.css('span.page-number.current::text').extract_first() == '1':
                for product in response.css('p.name.product-title a::attr(href)'):
                    yield response.follow(product, self.parse_object_and_save)
            else:
                page_href = str(response.css('a.page-number::attr(href)').extract_first())
                yield response.follow(page_href, self.follow_products)

    def follow_products(self, response):
        for product in response.css('p.name.product-title a::attr(href)').extract():
            yield response.follow(product, self.parse_object_and_save)

    def parse_object_and_save(self, response):
        title = response.css('h1.product-title.entry-title::text').extract_first().strip()
        description = ''
        for text in response.css('div#tab-description p') or response.css('div#tab-description ul li span.summary'):
            for extracted_text in text.css('::text').extract():
                if extracted_text != '':
                    description += extracted_text
        price = response.css('div.price-wrapper p.price.product-page-price span::text')[1].extract().strip()
        try:
            stock_response = response.css(
                'div.product-info.summary.entry-summary.col.col-fit.product-summary p.stock::text').extract_first().strip()
        except:
            stock_response = None
        if stock_response == 'Neturime':
            stock = 0
        elif stock_response == 'Turime':
            stock = 10
        else:
            stock = 1
        image_url = response.css(
            'figure.woocommerce-product-gallery__wrapper img.wp-post-image::attr(src)').extract_first()
        product_url = response.url
        purchase_url = product_url
        category_name = response.css('#product-sidebar ul li.current-cat a::text').extract_first()
        # category_link = response.css('#product-sidebar ul li.current-cat a::attr(href)').extract_first()
        yield {
            'title': f'<![CDATA[{title}]]>',
            'item_price': f'<![CDATA[{price}]]>',
            'manufacturer': '<![CDATA[Mindnutrition]]>',
            'image_url': f'<![CDATA[{image_url}]]>',
            'product_url': f'<![CDATA[{purchase_url}]]>',
            'categories': {'category' : f'<![CDATA[{category_name}]]>'},
            'description': f'<![CDATA[{description.strip()}]]>',
            'stock': f'<![CDATA[{stock}]]>',
            'ean_code': '',
            'manufacturer_code': '',
            'model': f'<![CDATA[{title}]]>'
        }

    def remove_chars_from_string(self, string, chars):
        bad_chars = chars
        for char in bad_chars:
            string = string.replace(char, '').strip()
        return string

fname = "kainos.xml"
Settings = get_project_settings()
Settings.update({'FEED_URI': fname})
if os.path.isfile(fname):
    os.remove(fname)
crawler = CrawlerProcess(Settings)
crawler.crawl(MySpider)
crawler.start()