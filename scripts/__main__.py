from congress_crawler import CongressCrawler
from markdown_builders import CongressMarkdownBuilder

if __name__ == "__main__":
    CongressCrawler().run()
    CongressMarkdownBuilder().run()
