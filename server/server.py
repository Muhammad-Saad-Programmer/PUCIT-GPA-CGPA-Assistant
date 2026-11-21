"""Serve the CGPA Guider tools over MCP."""

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
    mcp.run(transport="http", host="127.0.0.1", port=8000, path="/mcp")
