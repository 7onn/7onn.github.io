---
title: "GPG encryption and how to use it"
date: 2024-01-09T22:00:00+01:00
tags: [engineering, encryption, gpg, pgp, privacy]
author: Tom M G
draft: false
---

## Intro

GPG, which stands for GNU Privacy Guard, is an open source implementation of the [Pretty Good Privacy (PGP)][pgp-wiki] encryption standard. In this article, we'll focus on asymmetric encryption, where we use a set of two keys, one public to encrypt, and one private that only itself can decrypt the encrypted content.

## Creating a GPG key
### Generate your key pair
```bash
$ gpg --full-generate-key
...
gpg (GnuPG) 2.4.3; Copyright (C) 2023 g10 Code GmbH
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

Please select what kind of key you want:
   (1) RSA and RSA
   (2) DSA and Elgamal
   (3) DSA (sign only)
   (4) RSA (sign only)
   (9) ECC (sign and encrypt) *default*
  (10) ECC (sign only)
  (14) Existing key from card
Your selection? 1

RSA keys may be between 1024 and 4096 bits long.
What keysize do you want? (3072) 4096

Requested keysize is 4096 bits
Please specify how long the key should be valid.
         0 = key does not expire
      <n>  = key expires in n days
      <n>w = key expires in n weeks
      <n>m = key expires in n months
      <n>y = key expires in n years
Key is valid for? (0) 0

Key does not expire at all
Is this correct? (y/N) y

GnuPG needs to construct a user ID to identify your key.
Real name: John Doe
Email address: john.doe@somewhere.com
Comment: Personal encryption and signing GPG key

You selected this USER-ID:
    "John Doe (Personal encryption and signing GPG key) <john.doe@somewhere.com>"

Change (N)ame, (C)omment, (E)mail or (O)kay/(Q)uit? O

# One optional password will be prompted for the encryption key
We need to generate a lot of random bytes. It is a good idea to perform
some other action (type on the keyboard, move the mouse, utilize the
disks) during the prime generation; this gives the random number
generator a better chance to gain enough entropy.

# One optional password will be prompted for the signing key
We need to generate a lot of random bytes. It is a good idea to perform
some other action (type on the keyboard, move the mouse, utilize the
disks) during the prime generation; this gives the random number
generator a better chance to gain enough entropy.

gpg: revocation certificate stored as '~/.gnupg/openpgp-revocs.d/C49BCFA8706203B8A03BF3A22EC378BC8416920D.rev'
public and secret key created and signed.

pub   rsa4096 2024-01-10 [SC]
      C49BCFA8706203B8A03BF3A22EC378BC8416920D
uid                      John Doe (Personal encryption and signing GPG key) <john.doe@somewhere.com>
sub   rsa4096 2024-01-10 [E]
```

### Check for your key pair
```bash
$ gpg --list-signatures
...
~/.gnupg/pubring.kbx
-----------------------------
pub   rsa4096 2024-01-10 [SC]
      C49BCFA8706203B8A03BF3A22EC378BC8416920D
uid           [ultimate] John Doe (Personal encryption and signing GPG key) <john.doe@somewhere.com>
sig 3        2EC378BC8416920D 2024-01-10  [self-signature]
sub   rsa4096 2024-01-10 [E]
sig          2EC378BC8416920D 2024-01-10  [self-signature]
```

### Export your key pair
```bash
# Public key
$ gpg --armor --export 2EC378BC8416920D > john_doe_public_gpg_key.asc

# Private key
$ gpg --armor --export-secret-keys 2EC378BC8416920D > john_doe_private_gpg_key.asc
```

### Remove keys
Now that we have the key pair, let's store it somewhere safe and let's remove the keys to pretend we are importing someone else's key to encrypt something for them.
```bash
$ gpg --delete-keys 2EC378BC8416920D
...
pub  rsa4096/2EC378BC8416920D 2024-01-10 John Doe (Personal encryption and signing GPG key) <john.doe@somewhere.com>
Delete this key from the keyring? (y/N) y

$ gpg --delete-secret-keys 2EC378BC8416920D
...
sec  rsa4096/2EC378BC8416920D 2024-01-10 John Doe (Personal encryption and signing GPG key) <john.doe@somewhere.com>
Delete this key from the keyring? (y/N) y
This is a secret key! - really delete? (y/N) y
```

### Import public keys
Let's say you want to send to John Doe something that only they can read. You would import their public key like this:
```bash
$ gpg --import john_doe_public_gpg_key.asc
...
gpg: key 2EC378BC8416920D: public key "John Doe (Personal encryption and signing GPG key) <john.doe@somewhere.com>" imported
gpg: Total number processed: 1
gpg:               imported: 1
```

### Encrypt
With the public key available, you can encrypt some content as follows:
```bash
$ echo "my secret message" > not_so_secret_message.txt
$ gpg --encrypt --recipient 2EC378BC8416920D --output secret_message.txt.asc not_so_secret_message.txt

# Check for the encrypted content
$ cat secret_message.txt.asc
...
───────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
       │ File: secret_message.txt.asc
───────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1   │ �^B^L^C^L>�
   2   │ ��ѿ^A^P^@��9=^SJ�    ^X�-��^Y^Z���s��v[�x�^G�^OutI)rx�����n��ψHZI�����L^W�p e���Kyz^S��&��^Y?��9�רP��S��݈^m�is�<�B���q~^U����w^Nب�:^M����c]��[L�^?\�5�I�^Z�Q'�^V����^W�^@+�N�0�XF�ޜߋu�ݻ5�,�X9@��    ���$�^K�r�   ���N�&��}�
       │ �b�^Wkֿ#bXQp������^G^��VN�^U}(^Ro�m^K��^Y^B��r�Oy`��^G�s���>�m�$^R�U%^^^Z�^]ѥ{���}��O���t^QCI�-��]t����4v�D��7���^F�}):Y�-^Y_��^@�ۿX^W�^US�^B��^^^Z�Y���N��<�N!�3�^]�^R�_G^Xet������0^T^N^]^UH^E^?�h�yiB�
   3   │ h�c$ͤb�^BIЍ��^X�4��^@�>g�V����+=�*^]��|��WQ�x��^Fl��7��������q�^KQ�?�#����bf^PP ��d��%�̀u^Z�1�N^B�h�we^Y�^@,^A^^iA�$��p�  T'�k9�a�$��K^_��\H��[^Uԓ^A  ^B^P��ù y��^N������4R5��$\y���U��p��V�^V���bC}.�j�i`��^B��^Pb��^L^@�Ī
   4   │ �2�5��N��O�;�[ǆi]^Df�^~�W^D6W^O�ƔQ��խAl�^T�E��Q^C�^]`����~�^X�Խ���^�Zq�^Q��KːB�
───────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
```

Now, you can share the encrypted content with John Doe. Now imagine that they want to decrypt the message from a new computer and they would need to import their private key. They would do it like:
```bash
$ gpg --import john_doe_private_gpg_key.asc
...
gpg: key 2EC378BC8416920D: "John Doe (Personal encryption and signing GPG key) <john.doe@somewhere.com>" not changed
gpg: key 2EC378BC8416920D: secret key imported
gpg: Total number processed: 1
gpg:              unchanged: 1
gpg:       secret keys read: 1
gpg:   secret keys imported: 1
```

Once the secret key is on the keychain, the  decryption can be done as follows:
```bash
$ gpg --decrypt --output decrypted_message.txt secret_message.txt.asc

# See the original content
$ cat decrypted_message.txt
...
───────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
       │ File: decrypted_message.txt
───────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1   │ my secret message
───────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
```

## Using GPG as a security measure
Besides playing around with encrypted messages, GPG is used in another immensely useful feature in the routine of a software engineer or anyone using GitHub.

Let's look at an example of its capabilities. In GitHub, you can [store your public key][gpg-gh] and then use `~/.gitconfig` to specify which private key should be used to sign the commit.
```toml 
# ~/.gitconfig
[user]
    email = john.doe@somewhere.com
    name = John Doe
    signingkey = 0x2EC378BC8416920D
[commit]
    gpgsign = True
```

This local git configuration plus the `Flag unsigned commits as unverified` checked in the [aforementioned feature][gpg-gh] would display a `Verified` badge in all of your signed commits while making commits you did not sign `Unverified`. Such a feature would e.g. prevent [git-blame-someone-else][git-blame-someone-else] from being used against you like it was with Linus Torvalds 🤦

### An extra mile
GPG keys (and SSH keys too) can be stored on smart cards like a [Yubikey][gpg-yubikey]. This adds an extra layer of security by preventing the use of a file that can be stolen by some malware on your computer.

## Conclusion
- You should set a password for your keys
   - This ensures that even if the file is stolen, people pretending to be you won't be able to decrypt or sign anything on your behalf
- You should have a right to privacy
- Better safe than sorry

If you liked this article, import my [public GPG key][gpg-tom] and send me some encrypted message <3

[pgp-wiki]: https://en.wikipedia.org/wiki/Pretty_Good_Privacy
[gpg-gh]: https://github.com/settings/keys
[git-blame-someone-else]: https://github.com/jayphelps/git-blame-someone-else
[gpg-tom]: https://www.7onn.dev/tom.asc
[gpg-yubikey]: https://support.yubico.com/hc/en-us/articles/360013790259-Using-Your-YubiKey-with-OpenPGP
