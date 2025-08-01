import asyncio
import aiohttp
import json

async def test_company(session, name, i):
    data = {
        "entity_name": f"{name} Company {i}",
        "reporting_period": 2025,
        "lei": f"DEMO{i:016d}AB"
    }
    async with session.post('http://localhost:8000/api/v1/esrs-e1/export-ixbrl', 
                           json=data) as resp:
        if resp.status == 200:
            content = await resp.text()
            errors = content.count('error')
            facts = content.count('nonFraction') + content.count('nonNumeric')
            return f"✅ {name} {i}: {facts} facts, {errors} errors"
        return f"❌ {name} {i}: Failed"

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [test_company(session, "Test", i) for i in range(1, 11)]
        results = await asyncio.gather(*tasks)
        for r in results:
            print(r)

asyncio.run(main())
