# tompsh.github.io

personal blog and ~~for a while~~ something more

## run it locally
```bash
pip3 install -r requirements.txt
python3 ./scripts/
```

```bash
# https://gohugo.io/getting-started/installing/#debian-and-ubuntu
hugo serve
```

## deployment
this project currently bears two responsabilities
- webpage
  - it uses [hugo](https://gohugo.io/) to build my blog static files and [github actions](https://github.com/tompsh/tompsh.github.io/blob/main/.github/workflows/gh-pages.yml) to deploy it 
- webcrawlers
  - it relies on [github actions](https://github.com/tompsh/tompsh.github.io/blob/main/.github/workflows/update-contacts.yml) to perform daily web data crawlings at [congress](https://www.camara.leg.br/), [senate](https://www25.senado.leg.br/) and [federal court of justice]()
