#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2016 Igalia S.L.
#
# Distributed under terms of the AGPLv3 license.

import lasso, pyotp, passgen


Username = lasso.StringMatch(r"^[a-zA-Z][a-zA-Z0-9_\.]+$",
        error="Invalid username")
Password = lasso.And(str, lambda l: len(l) >= 8,
        error="Password must be at least 8 chracters")
OTPToken = lasso.And(str, lambda l: len(l) == 6,
        error="Invalid OTP token")
OTPKey = lasso.And(str, lambda l: len(l) == 16,
        error="Invalid OTP key")


class User(lasso.Schemed):
    __schema__ = {
        "name"    : lasso.And(str, lambda l: len(l) > 0),
        "username": Username,
        "password": Password,
        "totp_key": OTPKey,
    }

    def __init__(self, username, password=None, name=None, totp_key=None):
        if name is None:
            name = username
        if password is None:
            password = passgen.passgen()
        if totp_key is None:
            totp_key = pyotp.random_base32()
        super(User, self).__init__(username=username, password=password,
                name=name, totp_key=totp_key)

    def __repr__(self):
        return "{!s}({!r})".format(self.__class__.__name__, self.username)

    def totp_verify(self, totp_token):
        return pyotp.TOTP(self.totp_key).verify(totp_token)

    def totp_uri(self, issuer=None):
        return pyotp.TOTP(self.totp_key).provisioning_uri(self.username, issuer)



class Formed(lasso.Schemed):
    @classmethod
    def from_form(cls, data):
        d = {}
        # XXX: _schema is an implementation detail :|
        for k in cls.__schema__._schema.keys():
            if k in data:
                d[k] = data[k]

        try:
            return cls.validate(d), None
        except lasso.SchemaError as e:
            return None, e.message


class LoginForm(Formed):
    __schema__ = {
        "username": Username,
        "password": Password,
        "otptoken": OTPToken,
    }
