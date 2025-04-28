import asyncio
import aiohttp
import random

from models import create_login, get_login1

# List of User-Agent strings to rotate
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",
    # Add more User-Agents as needed
]

url = "https://login.emaktab.uz"
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
}


async def login_request(session, login, user_agent):
    """Helper function to perform a single login request with rotating user-agent"""
    headers["User-Agent"] = user_agent  # Set random user-agent for this request

    async with session.post(url, headers=headers, data={"login": login.login, "password": login.password}) as response:
        if len(response.cookies) == 4:
            status = True
        else:
            status = False
        await create_login(login=login.login, password=login.password, status=status,
                           school_number=login.school_number, type=login.type)
        return login.login, login.password, status, login.school_number, login.type


async def login():
    wrong_logins = ''
    logins = await get_login1()
    l = 0
    semaphore = asyncio.Semaphore(20)  # Limit to 20 concurrent requests
    tasks = []

    # Rotate User-Agent after every 50 requests globally
    user_agent_idx = 0

    async with aiohttp.ClientSession() as session:
        for idx, login in enumerate(logins):
            # Rotate User-Agent every 50 requests
            if idx % 50 == 0:
                user_agent_idx = (user_agent_idx + 1) % len(user_agents)

            user_agent = user_agents[user_agent_idx]
            tasks.append(login_request(session=session, login=login, user_agent=user_agent))  # Pass user-agent here

        results = await asyncio.gather(*tasks)

    for login_data in results:
        login, password, status, school_number, type = login_data
        if not status:
            wrong_logins += f"🔑 Login: {login} | Password: {password}_{school_number}_{type}\n,"
        else:
            l += 1

    return wrong_logins, l


async def login_main2(session, data, semaphore, user_agent):
    async with semaphore:
        login, password = data.split(':', 1)
        headers["User-Agent"] = user_agent  # Set random user-agent for this request

        async with session.post(url, data={"login": login, "password": password}, headers=headers) as response:
            cookies = response.cookies
            if len(cookies) < 4:
                return f"{login}:{password}"
    return None


async def login_main(data_list, type, school_number):
    semaphore = asyncio.Semaphore(20)  # Limit to 20 concurrent requests
    tasks = []

    # Rotate User-Agent after every 50 requests globally
    user_agent_idx = 0

    async with aiohttp.ClientSession() as session:
        for idx, data in enumerate(data_list):
            # Rotate User-Agent every 50 requests
            if idx % 50 == 0:
                user_agent_idx = (user_agent_idx + 1) % len(user_agents)

            user_agent = user_agents[user_agent_idx]
            tasks.append(login_main2(session=session, data=data, semaphore=semaphore,
                                     user_agent=user_agent))  # Pass user-agent here

        results = await asyncio.gather(*tasks, return_exceptions=True)

    failed_logins = list(filter(None, results))  # Only keep failed logins
    successful_logins = []

    for data in data_list:
        parts = data.split(':')
        if len(parts) > 2:
            school_number = parts[2]
        if data not in failed_logins:
            successful_logins.append(data)
            await create_login(login=data.split(':')[0], password=data.split(':')[1], status=True,
                               school_number=school_number, type=type)

    return failed_logins, successful_logins
