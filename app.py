#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2016 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

import muffin
from passgen import passgen
from store import TacitumStore
from os import path as P


app = muffin.Application("tacitum",
        PLUGINS = ("muffin_session", "muffin_pystache"),
        SESSION_LOGIN_URL = "/login",
        SESSION_SECRET = passgen(),
        PYSTACHE_PATH = P.join(P.dirname(__file__), "templates"),
        PYSTACHE_LAYOUT = "layout",
    )

store = TacitumStore("data")


@app.ps.session.user_loader
def get_user(uid):
    return store.get("/user/" + uid)


@app.register("/login", methods="GET")
def login(request):
    return app.ps.pystache.render("login", page_title="Login")


@app.register("/login", methods="POST")
def login_post(request):
    data = yield from request.post()
    user = store.get("/user/" + data.get("username"))
    errmsg = None
    if user is None:
        errmsg = "Invalid user name."
    elif user.password != data.get("password"):
        errmsg = "Invalid password."
    elif not user.totp_verify(data.get("otptoken")):
        errmsg = "Invalid token."
    else:
        yield from app.ps.session.login(request, user.username)
        return muffin.HTTPFound("/")

    return app.ps.pystache.render("login", page_title="Login",
            username=data.get("username"), error_message=errmsg)


@app.register("/logout")
def logout(request):
    yield from app.ps.session.logout(request)
    return muffin.HTTPFound("/")

@app.register("/")
@app.ps.session.user_pass()
def index(request):
    return app.ps.pystache.render("dashboard", title="Dashboard",
            user=request.user)
