#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import tempfile
import subprocess
from Crypto.PublicKey import RSA
from lib.rsalibnum import invmod

logger = logging.getLogger("global_logger")


def generate_pq_from_n_and_p_or_q(n, p=None, q=None):
    """ Return p and q from (n, p) or (n, q)
    """
    if p is None:
        p = n // q
    elif q is None:
        q = n // p
    return (p, q)


def generate_keys_from_p_q_e_n(p, q, e, n):
    """ Generate keypair from p, q, e, n
    """
    priv_key = None
    try:
        priv_key = PrivateKey(p, q, e, n)
    except (ValueError, TypeError):
        pass

    pub_key = RSA.construct((n, e)).publickey().exportKey()
    return (pub_key, priv_key)


class PublicKey(object):
    def __init__(self, key, filename=None):
        """Create RSA key from input content
           :param key: public key file content
           :type key: string
        """
        try:
            pub = RSA.importKey(key)
        except ValueError as e:
            logger = logging.getLogger("global_logger")
            logger.critical("Key format not supported.")
            exit(1)
        self.filename = filename
        self.n = pub.n
        self.e = pub.e
        self.key = key

    def __str__(self):
        """Print armored public key
        """
        return self.key


class PrivateKey(object):
    def __init__(self, p, q, e, n):
        """Create private key from base components
           :param p: extracted from n
           :param q: extracted from n
           :param e: exponent
           :param n: n from public key
        """
        self.p = p
        self.q = q
        self.e = e
        self.n = n
        t = (p - 1) * (q - 1)
        d = invmod(e, t)
        self.key = RSA.construct((n, e, d, p, q))
        self.d = self.key.d

    def decrypt(self, cipher):
        """Uncipher data with private key
           :param cipher: input cipher
           :type cipher: string
        """

        try:
            tmp_priv_key = tempfile.NamedTemporaryFile()
            with open(tmp_priv_key.name, "wb") as tmpfd:
                tmpfd.write(str(self).encode("utf8"))
            tmp_priv_key_name = tmp_priv_key.name

            tmp_cipher = tempfile.NamedTemporaryFile()
            with open(tmp_cipher.name, "wb") as tmpfd:
                tmpfd.write(cipher)
            tmp_cipher_name = tmp_cipher.name

            with open("/dev/null") as DN:
                openssl_result = subprocess.check_output(
                    [
                        "openssl",
                        "rsautl",
                        "-raw",
                        "-decrypt",
                        "-in",
                        tmp_cipher_name,
                        "-inkey",
                        tmp_priv_key_name,
                    ],
                    stderr=DN,
                )
                return openssl_result
        except:
            return self.key.decrypt(cipher)

    def __str__(self):
        """Print armored private key
        """
        return self.key.exportKey().decode("utf-8")
