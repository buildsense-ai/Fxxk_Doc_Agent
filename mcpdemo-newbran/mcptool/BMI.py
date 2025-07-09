from mcp.server.fastmcp import FastMCP

mcp=FastMCP("MCP SERVER")

@mcp.tool()
def calculate_bmi(weight: float, height: float) -> float:
    """
    Calculate BMI
    """
    return weight / (height ** 2)