from congress_crawler import CongressCrawler
from markdown_builders import CongressMarkdownBuilder, SenateMarkdownBuilder
from senate_crawler import SenateCrawler

if __name__ == "__main__":
    SenateCrawler().run()
    SenateMarkdownBuilder().run()
    CongressCrawler().run()
    CongressMarkdownBuilder().run()
