import asyncio
import aiohttp
import time
import random
import uuid

API_URL = "http://localhost:8000"
NUM_USERS = 10
JOBS_PER_USER = 100 # Total 1000 jobs

async def worker(session, user_email, user_id, token):
    headers = {"Authorization": f"Bearer {token}"}
    
    start_time = time.time()
    
    for i in range(JOBS_PER_USER):
        idempotency_key = str(uuid.uuid4())
        payload = {
            "idempotency_key": idempotency_key,
            "language": "python",
            "code": "print('Load Test {}'.format({}))".format(i),
            "priority": random.choice([0, 1])
        }
        
        try:
            async with session.post(f"{API_URL}/jobs/", json=payload, headers=headers) as resp:
                if resp.status == 429:
                    # Rate limit exceeded
                    await asyncio.sleep(1)
                    continue
                resp_json = await resp.json()
        except Exception as e:
            pass

    end_time = time.time()
    return end_time - start_time

async def main():
    async with aiohttp.ClientSession() as session:
        # Register users
        tokens = []
        for i in range(NUM_USERS):
            email = f"loaduser{i}@test.com"
            try:
                # Register
                await session.post(f"{API_URL}/auth/register", json={"email": email, "password": "password"})
            except:
                pass
            
            # Login
            data = {"username": email, "password": "password"}
            async with session.post(f"{API_URL}/auth/token", data=data) as resp:
                if resp.status == 200:
                    body = await resp.json()
                    tokens.append(body["access_token"])
        
        print(f"Registered and got {len(tokens)} tokens. Starting load generation...")
        
        tasks = []
        for idx, token in enumerate(tokens):
            tasks.append(worker(session, f"user{idx}", f"id_{idx}", token))
            
        results = await asyncio.gather(*tasks)
        print("Completed load generation.")
        print("Average time per user to submit jobs:", sum(results)/len(results) if results else 0)

if __name__ == "__main__":
    asyncio.run(main())
