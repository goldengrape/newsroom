import re

with open("src/newsroom/filtering.py", "r") as f:
    content = f.read()

old_func = """def parse_date(date_str: str) -> datetime.datetime:
    try:
        return email.utils.parsedate_to_datetime(date_str)
    except (ValueError, TypeError):
        try:
            return datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            # Fallback to current time if unparseable
            return datetime.datetime.now(datetime.timezone.utc)"""

new_func = """def parse_date(date_str: str) -> datetime.datetime:
    try:
        dt = email.utils.parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except (ValueError, TypeError):
        try:
            dt = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt
        except (ValueError, TypeError):
            # Fallback to current time if unparseable
            return datetime.datetime.now(datetime.timezone.utc)"""

if old_func in content:
    content = content.replace(old_func, new_func)
    with open("src/newsroom/filtering.py", "w") as f:
        f.write(content)
    print("Success")
else:
    print("Function not found, using regex...")
    # fallback if whitespace differs
    pattern = r"def parse_date.*?return datetime.datetime.now\(datetime.timezone.utc\)"
    content = re.sub(pattern, new_func, content, flags=re.DOTALL)
    with open("src/newsroom/filtering.py", "w") as f:
        f.write(content)
    print("Regex replacement success")
