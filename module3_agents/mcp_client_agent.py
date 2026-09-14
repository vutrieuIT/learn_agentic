import asyncio, sys, json
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from shared.llm_client import LLMClient

SERVER = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).parent / "mcp_server.py")])

async def mcp_tools_spec(session: ClientSession) -> list[dict]:
    listed = await session.list_tools()
    # convert format MCP (name/description/input_schema) -> format OpenAI function-calling
    # (giống hệt TOOLS_SPEC bạn tự viết tay ở bước 1, chỉ khác nguồn sinh ra)
    return [{"type": "function", "function": {
                "name": t.name, "description": t.description, "parameters": t.input_schema}}
            for t in listed.tools]

async def run(user_msg: str, max_steps: int = 6) -> str:
    llm = LLMClient()
    async with stdio_client(SERVER) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools_spec = await mcp_tools_spec(session)
        print("tool khám phá được từ server:", [t["function"]["name"] for t in tools_spec])

        messages = [
            {"role": "system", "content": "Bạn là trợ lý tính chi phí chuyến đi. "
                                           "CHỈ dùng số liệu từ tool, không tự đoán."},
            {"role": "user", "content": user_msg},
        ]
        for step in range(max_steps):
            result = llm.chat(messages, tools=tools_spec, tool_choice="auto")
            assistant_msg = {"role": "assistant", "content": result.content or None}
            if result.tool_calls:
                assistant_msg["tool_calls"] = [tc.model_dump() for tc in result.tool_calls]
            messages.append(assistant_msg)

            if not result.tool_calls:
                return result.content

            for call in result.tool_calls:
                args = json.loads(call.function.arguments)
                # <-- điểm khác biệt duy nhất so với Agent gốc: gọi qua session, không qua dict local
                out = await session.call_tool(call.function.name, args)
                content = out.content[0].text if out.content else "{}"
                print(f"  [step {step}] {call.function.name}({args}) -> {content}")
                messages.append({"role": "tool", "tool_call_id": call.id, "content": content})

        return "[hết max_steps]"

if __name__ == "__main__":
    answer = asyncio.run(run("Tôi đi từ Hà Nội đến Đà Nẵng bằng xe máy tiêu thụ 3 lít/100km, tốn bao nhiêu tiền xăng?"))
    print("\n--- trả lời ---")
    print(answer)