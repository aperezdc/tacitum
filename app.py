#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2016 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

import muffin
import models, lasso
from passgen import passgen
from store import TacitumStore
from os import path as P


app = muffin.Application("tacitum",
        PLUGINS = ("muffin_session", "muffin_pystache"),
        SESSION_LOGIN_URL = "/login",
        SESSION_SECRET = passgen(),
        STATIC_FOLDERS = P.join(P.dirname(__file__), "static"),
        PYSTACHE_PATH = P.join(P.dirname(__file__), "templates"),
        PYSTACHE_LAYOUT = "layout",
    )

store = TacitumStore("data")

from aiomanhole import start_manhole
app.register_on_start(lambda _: start_manhole(
        banner="<<< Tacitum >>>\n", path="/tmp/tacitum.manhole",
        namespace={"app": app, "store": store, "models": models}))


@app.ps.session.user_loader
def get_user(uid):
    return store.get("/user/" + uid)


@app.register("/login", methods="GET")
def login(request):
    return app.ps.pystache.render("login", page_title="Login")


@app.register("/login", methods="POST")
def login_post(request):
    data = yield from request.post()

    user = store.get("/user/" + data.get("username", ""))
    if user is None:
        return app.ps.pystache.render("login", page_title="Login",
                error_message="Invalid user name.")

    data, errmsg = models.LoginForm.from_form(data)
    if data is None:
        pass
    elif user.password != data.password:
        errmsg = "Invalid password."
    elif not user.totp_verify(data.otptoken):
        errmsg = "Invalid token."
    else:
        yield from app.ps.session.login(request, user.username)
        return muffin.HTTPFound("/")

    return app.ps.pystache.render("login", page_title="Login",
            username=(data.username if data else ""), error_message=errmsg)


@app.register("/logout")
def logout(request):
    yield from app.ps.session.logout(request)
    return muffin.HTTPFound("/")


@app.register("/")
@app.ps.session.user_pass()
def index(request):
    return app.ps.pystache.render("dashboard", title="Dashboard",
            user=request.user)


@app.register("/qr/totp.png")
@app.ps.session.user_pass()
def qr_totp_png(request):
    # FIXME: Potentially slow.
    import pyqrcode
    from io import BytesIO
    code = pyqrcode.create(request.user.totp_uri())
    data = BytesIO()
    code.png(data, scale=8)
    return muffin.Response(content_type="image/png", body=data.getvalue())
