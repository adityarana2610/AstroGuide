from astroguide.tools.birth_chart import get_birth_chart
from astroguide.tools.numbers_stones import get_numbers_and_stones

print(type(get_birth_chart))
try:
    res = get_numbers_and_stones.invoke({"birth_date": "2000-01-01"})
    print("Invoke worked:", list(res.keys()))
except Exception as e:
    print("Invoke failed:", e)

try:
    res2 = get_numbers_and_stones("2000-01-01")
    print("Direct call worked")
except Exception as e:
    print("Direct call failed:", e)
