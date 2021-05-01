import pandas as pd


class CongressMarkdownBuilder:
    def __init__(self):
        self.html = ""
        self.links = []
        self.mailtos = {}
        self.df_congresspeople = pd.read_csv("congresspeople.csv").sort_values("party")

    def build_html(self):
        self.html = """
---
title: "Envie seu email aos representantes no congresso"
date: 2021-04-29T21:01:00-03:00
tags: [politics, congress, email]
author: tom
draft: false
---
<h1>Escolha o partido</h1>
"""
        for link in self.links:
            self.html = self.html + link

        f = open("./content/post/congress.md", "w")
        f.write(self.html)
        f.close()

    def build_links(self):
        for party in self.mailtos:
            link = '<h2><a href="mailto:'
            for email in self.mailtos[party]:
                link = link + email
            link = (
                link
                + '"> '
                + party
                + "("
                + str(len(self.mailtos[party].split(",")) - 1)
                + ") </a></h2>"
            )

            self.links.append(link)

    def run(self):
        emails = ""
        party = ""
        for _, row in self.df_congresspeople.iterrows():
            emails = emails + row["email"] + ","
            if row["party"] != party:
                self.mailtos[row["party"]] = emails
                emails = ""
            party = row["party"]

        self.build_links()
        self.build_html()
        print(self.html)
