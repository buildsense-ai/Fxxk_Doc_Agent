from mcp.server.fastmcp import FastMCP

mcp=FastMCP("hello world")

@mcp.tool()
def hello(name:str):
    return {"message":f"Hello {name}"}