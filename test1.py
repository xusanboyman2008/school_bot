import aiohttp
import asyncio

from models import create_login

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
}

# Define the login URL
LOGIN_URL = "https://login.emaktab.uz/"

async def login_request(session, login):
    """Helper function to perform a single login request"""
    async with session.post(LOGIN_URL, headers=headers, data={"login": login["login"], "password": login["password"]}) as response:
        status = len(response.cookies) == 4  # Fixed logic
        await create_login(
            login=login["login"], password=login["password"],
            status=status, school_number=login.get("school_number"), type=login.get("type")
        )
        if not status:
            return login["login"], login["password"], status, login.get("school_number"), login.get("type")
        return login["login"], login["password"], status, login.get("school_number"), login.get("type")

async def login():
    wrong_logins = ''
    logins = [{"password": "12345678x", "login": "xusanboyabdulxayev"}]  # Changed to list of dicts
    l = 0

    async with aiohttp.ClientSession() as session:
        tasks = [login_request(session, login) for login in logins]
        results = await asyncio.gather(*tasks)

    for login_data in results:
        print(login_data)
        if login_data:  # Ensure we don't unpack None
            login, password, status, school_number, type_ = login_data
            if not status:
                wrong_logins += f"🔑 Login: {login} | Password: {password} | School: {school_number} | Type: {type_}\n"
            else:
                l += 1
    print('asda',wrong_logins,l)
    return wrong_logins, l

async def main():
    wrong_logins, success_count = await login()
    if wrong_logins:
        print("Login failed for:\n", wrong_logins)
    else:
        print(f"All logins successful! ({success_count} logins)")

# Run the async main function
asyncio.run(main())
