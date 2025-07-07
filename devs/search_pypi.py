import requests

def find_erispulse_module_packages():
    url = "https://pypi.org/search/"
    params = {
        "q": '"erispulse.module"',
        "page": 1
    }
    
    response = requests.get(url, params=params)
    results = response.json()
    
    for result in results.get("results", []):
        print(result["name"])
        