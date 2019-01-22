import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import os
import hashlib


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
                page_href = str(response.css(
                    'a.page-number::attr(href)').extract_first())
                yield response.follow(page_href, self.follow_products)

    def follow_products(self, response):
        for product in response.css('p.name.product-title a::attr(href)').extract():
            yield response.follow(product, self.parse_object_and_save)

    def parse_object_and_save(self, response):
        title = response.css(
            'h1.product-title.entry-title::text').extract_first().strip()
        description = response.css('#tab-description').extract_first()
        wrongPrice = response.css(
            'div.price-wrapper p.price.product-page-price del span::text')

        if len(wrongPrice) > 0:
            price = response.css(
                'div.price-wrapper p.price.product-page-price ins span::text')[1].extract().strip()
        else:
            price = response.css(
                'div.price-wrapper p.price.product-page-price span::text')[1].extract().strip()

        image_url = response.css(
            'figure.woocommerce-product-gallery__wrapper img.wp-post-image::attr(src)').extract_first()
        product_url = response.url
        purchase_url = product_url
        category_name = response.css(
            '#product-sidebar ul li.current-cat a::text').extract_first()
        item_id = int(hashlib.sha256(title.encode(
            'utf-8')).hexdigest(), 16) % 10 ** 8
        try:
            quantityStr = response.css(
                "input.input-text.qty.text::attr('max')").extract_first()
            quantity = int(quantityStr)
        except:
            quantity = 1
        yield {
            'url': f'<![CDATA[{purchase_url}]]>',
            'id': item_id,
            'categories': {'category': f'<![CDATA[{category_name}]]>'},
            'title': f'<![CDATA[{title}]]>',
            'description': f'<![CDATA[{description.strip()}]]>',
            'price': float(price),
            'prime_costs': int(float(price)*0.8),
            'images': {'image': f'<![CDATA[{image_url}]]>'},
            'quantity': quantity
        }

    def remove_chars_from_string(self, string, chars):
        bad_chars = chars
        for char in bad_chars:
            string = string.replace(char, '').strip()
        return string


fname = "varle.xml"
Settings = get_project_settings()
Settings.update({'FEED_URI': fname})
if os.path.isfile(fname):
    os.remove(fname)
crawler = CrawlerProcess(Settings)
crawler.crawl(MySpider)
crawler.start()
