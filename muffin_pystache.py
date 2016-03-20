#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2016 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

from muffin.plugins import BasePlugin, PluginException
from muffin.utils import to_coroutine
from pystache import Renderer
from asyncio import coroutine
from os import path as P


class Plugin(BasePlugin):
    name = "pystache"

    defaults = dict(
        path = ("templates",),
        extension = "mustache",
        encoding = "utf-8",
        partials = None,
        layout = None,
    )

    def __init__(self, **options):
        super().__init__(**options)
        self.renderer = None

    def setup(self, app):
        super().setup(app)

        if isinstance(self.cfg.path, str):
            self.cfg.path = [self.cfg.path]
        self.cfg.path = [P.abspath(p) for p in self.cfg.path]
        self.renderer = Renderer(file_encoding=self.cfg.encoding,
                search_dirs=self.cfg.path,
                file_extension=self.cfg.extension,
                partials=self.cfg.partials)

    @coroutine
    def render(self, path, layout=None, *ctx, **kw):
        layout = self.cfg.layout if layout is None else layout
        if layout:
            kw["yield"] = self.renderer.render_name(path, *ctx, **kw)
            path = layout
        return self.renderer.render_name(path, *ctx, **kw)
