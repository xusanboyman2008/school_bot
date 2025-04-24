import asyncio

import aiohttp

from models import create_login, get_login1

url = "https://login.emaktab.uz"
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36"
}
async def login_request(session, login):
    """Helper function to perform a single login request"""
    async with session.post(url, headers=headers, data={"login": login.login, "password": login.password}) as response:
        if len(response.cookies) == 4:
            status = True
        else:
            status = False
        await create_login(login=login.login, password=login.password, status=status,school_number=login.school_number,type=login.type)
        return login.login, login.password, status,login.school_number,login.type


async def login():
    wrong_logins = ''
    logins = await get_login1()
    l = 0
    async with aiohttp.ClientSession() as session:
        tasks = [login_request(session, login) for login in logins]
        results = await asyncio.gather(*tasks)
    for login_data in results:
        login, password, status, school_number,type = login_data
        if not status:
            wrong_logins += f"🔑 Login: {login} | Password: {password}_{school_number}_{type}\n,"
        else:
            l += 1
    return wrong_logins, l


async def login_main2(session, data, semaphore):
    async with semaphore:
        login, password = data.split(':', 1)
        async with session.post(url, data={"login": login, "password": password}) as response:
            cookies = response.cookies
            print(len(cookies))
            if len(cookies) < 4:
                return f"{login}:{password}"
    return None


async def login_main(data_list, type, school_number):
    semaphore = asyncio.Semaphore(20)  # Limit to 20 concurrent requests
    async with aiohttp.ClientSession() as session:
        tasks = [login_main2(session, data, semaphore) for data in data_list]
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

