import pandas as pd


class WebpageBuilder:
    def __init__(self):
        self.html = ''
        self.links = []
        self.mailtos = {}
        self.df_congresspeople = pd.read_csv(
            "congresspeople.csv").sort_values('party')

    def build_html(self):
        self.html = '''
        <html>

        <head>
        <meta charset='utf-8'>
        <meta http-equiv='X-UA-Compatible' content='IE=edge'>
        <title>vacilao vai ser cobrado</title>
        <meta name='viewport' content='width=device-width, initial-scale=1'>
        <link rel='stylesheet' type='text/css' media='screen' href='main.css'>
        <script src='main.js'></script>
        </head>
        <body>
        <h1>camara des deputades</h1>
        '''
        for link in self.links:
            self.html = self.html + link

        self.html = self.html + '''
        </body>
        </html>
        '''
        f = open("./index.html", "w")
        f.write(self.html)
        f.close()

    def build_links(self):
        for party in self.mailtos:
            link = '<h2><a href="mailto:'
            for email in self.mailtos[party]:
                link = link + email
            link = link + '"> ' + party + \
                '(' + \
                str(len(self.mailtos[party].split(","))-1) + ') </a></h2>'

            self.links.append(link)

    def run(self):
        emails = ''
        party = ''
        for _, row in self.df_congresspeople.iterrows():
            emails = emails + row['email'] + ','
            if row['party'] != party:
                self.mailtos[row['party']] = emails
                emails = ''
            party = row['party']

        self.build_links()
        self.build_html()

        print(self.html)
