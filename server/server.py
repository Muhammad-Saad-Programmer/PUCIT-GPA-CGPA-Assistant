"""Serve the CGPA Guider tools over MCP."""

import os

from fastmcp import FastMCP
import tools

mcp = FastMCP("cgpa")
mcp.tool(tools.marks_to_grade_points)
mcp.tool(tools.calculate_semester_gpa)
mcp.tool(tools.calculate_new_cgpa)
mcp.tool(tools.required_gpa_for_target)
mcp.tool(tools.get_semester_courses)
mcp.tool(tools.get_remaining_credit_hours)
mcp.tool(tools.save_report)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
        path="/mcp",
    )
