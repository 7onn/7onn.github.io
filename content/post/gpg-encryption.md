---
title: "GPG encryption and how to use it"
date: 2024-01-09T22:00:00+01:00
tags: [engineering, encryption, gpg, pgp, privacy]
author: Tom M G
draft: true
---

GPG, which stands for GNU Privacy Guard, is an open-source implementation of the [Pretty Good Privacy (PGP)][pgp-wiki] encryption standard. In this article, we'll focus on asymmetric encryption, where we use a set of two keys, one public to encrypt, and one private that only itself can decrypt some content.



Let's observe one example of some of its capabilities. In GitHub, one can [store their public key][gpg-gh] and then, via `~/.gitconfig`, set which private key should be used to sign the commit.

```toml 
# ~/.gitconfig
[user]
    email = bar@foo.com
    name = Foo Bar
    signingkey = 0x00000000000000000
[commit]
    gpgsign = True
```

The signing 


[pgp-wiki]: https://en.wikipedia.org/wiki/Pretty_Good_Privacy
[gpg-gh]: https://github.com/settings/keys
