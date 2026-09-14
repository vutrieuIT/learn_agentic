from mcp.server.mcpserver import MCPServer

mcp = MCPServer("trip-cost")

@mcp.tool()
def get_distance(city_a: str, city_b: str) -> dict:
    """Lấy khoảng cách (km) giữa 2 thành phố Việt Nam."""
    fake = {("Hà Nội", "Đà Nẵng"): 760, ("Hà Nội", "Sài Gòn"): 1700}
    km = fake.get((city_a, city_b)) or fake.get((city_b, city_a)) or 500
    return {"distance_km": km}

@mcp.tool()
def get_fuel_price() -> dict:
    """Lấy giá xăng hiện tại (VND/lít)."""
    return {"price_per_liter_vnd": 23000}

@mcp.tool()
def calc_cost(distance_km: float, price_per_liter: float, consumption_per_100km: float) -> dict:
    """Tính tổng tiền xăng = quãng đường * mức tiêu thụ / 100 * giá xăng.
    LUÔN dùng tool này để tính, không tự nhẩm."""
    liters = distance_km * consumption_per_100km / 100
    return {"total_vnd": round(liters * price_per_liter)}

if __name__ == "__main__":
    mcp.run(transport="stdio")   # giao tiếp qua stdin/stdout — cách phổ biến nhất cho local MCP server