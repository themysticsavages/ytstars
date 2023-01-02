import requests

from lupa import LuaRuntime
from luaparser import ast
from bs4 import BeautifulSoup
from bs4.element import Tag

lua = LuaRuntime()
sandbox = lua.require("sandbox")[0]

with open("./test.lua", encoding="utf-8") as fh:
    source = fh.read()

with open("./mock.lua", encoding="utf-8") as fh:
    mock = fh.read()


def entrypoint_source(script):
    """Read the inner contents of the entrypoint function"""
    tree = ast.parse(script)
    return ast.to_lua_source(
        tree.to_json()["Chunk"]["body"]
        .to_json()["Block"]["body"][0]
        .to_json()["Function"]["body"]
    )


# mock window and run source script to validate security
try:
    content = f"""{mock}
    {entrypoint_source(source)}
    """

    sandbox.run(content)
except Exception as e:
    raise Exception(e) from None

class Element:
    """Element with some simple methods"""
    def __init__(self, element: Tag):
        self.element = element
    def text(self):
        return self.element.text.encode("latin-1", errors="replace")

class Window:
    """Window object which is sent back with requests"""
    def __init__(self, soup: BeautifulSoup):
        self.soup = soup

    def select_all(self, selector):
        """Find all elements with a query selector"""
        return lua.table(*(Element(element) for element in self.soup.select(selector)))

    def select_one(self, selector):
        """Find one element with a query selector"""
        return Element(self.soup.select_one(selector))

class Request:
    """The Window object emulated from within Lua"""
    def wrap_(self, req, html):
        """Private function to convert request to either JSON or HTML"""
        if html == True:
            return Window(BeautifulSoup(req.text, "html.parser"))
        return req.json()

    def go(self, method, url, body=None, html=False):
        """Wrapper to request a URL"""
        if method != "GET":
            if body is not None:
                body = dict(map(lambda i, j: (i, j), body.keys(), body.values()))
            res = requests.request(method, url, json=body, timeout=10)
            return self.wrap_(res, html)

        res = requests.request(method, url, timeout=10)
        return self.wrap_(res, html)

request = Request()
response = lua.execute(
    f"""{source}
return main
"""
)(request)

print(response)
