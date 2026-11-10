# 🌍 সার্ভার IP দেশ (DB-IP)

এই ফোল্ডারের দুটি ফাইল প্লেলিস্টের সার্ভার IP → দেশ ম্যাপিংয়ের জন্য ব্যবহৃত হয়।

| ফাইল | কী আছে |
| --- | --- |
| `ip2country-v4.tsv.gz` | ইন্টারনেটের প্রতিটি IPv4 রেঞ্জের শুরুর ঠিকানা ও দেশের ISO কোড |
| `ip2country-v6.tsv.gz` | একই তথ্য IPv6 রেঞ্জের জন্য |

ফরম্যাট: প্রতি লাইনে `শুরুর-ঠিকানা<TAB>দেশের-কোড`। রেঞ্জের শেষ ঠিকানা আলাদা করে
লেখা হয় না — পরের লাইনের শুরুর ঠিকানাই আগের রেঞ্জের সীমা নির্ধারণ করে, তাই একটি
বাইনারি সার্চেই দেশ পাওয়া যায়। ফাইলের শুরুতে `#` দিয়ে লেখা মন্তব্য আছে।

## ডেটার উৎস ও লাইসেন্স

- ডেটা: **DB-IP IP to Country Lite** (স্ন্যাপশট ২০২৬-০৬-০১), লাইসেন্স [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)।
- পুনঃপ্রকাশ: [sapics/ip-location-db](https://github.com/sapics/ip-location-db) (`dbip-country`)। ডেটা DB-IP.com থেকে নেওয়া।
- অ্যাট্রিবিউশন: **IP Geolocation by DB-IP** — <https://db-ip.com>

প্লেলিস্ট বা এই টুল ব্যবহার করে কোনো ফলাফল প্রকাশ করলে উপরের অ্যাট্রিবিউশনটি রাখতে হবে।

## কনফিগারেশন

- `config.yaml` → `output.by_server_country`: দেশভিত্তিক ফাইল কোথায় লেখা হবে।
- `config.yaml` → `output.countries: false`: দেশভিত্তিক আউটপুট বন্ধ করে শুধু
  `FINAL_ULTIMATE_LIVE_CHECKED.m3u` লিখতে।
- `-1` ছাড়া অন্য কোড (যেমন `XX`) মানে ঠিকানাটি খোলা ইন্টারনেটের নয় (প্রাইভেট/রিজার্ভড)
  বা সূচিতে নেই — তখনই চ্যানেলটি "অজানা সার্ভার" দলে যায়।

## সূচি নতুন করে বানানো

```bash
curl -sSL -o ip-location-db.tgz \
  https://codeload.github.com/sapics/ip-location-db/tar.gz/refs/heads/main
mkdir -p ip-location-db
tar xzf ip-location-db.tgz -C ip-location-db --strip-components=1 \
  ip-location-db-main/dbip-country
python tools/build_country_index.py \
  --dbip-dir ip-location-db/dbip-country --snapshot 2026-06-01
```

স্ক্রিপ্টটির জন্য শুধু Python স্ট্যান্ডার্ড লাইব্রেরি দরকার; আউটপুট ফাইল দুটি
`src/data/`-এ লেখা হয় এবং `tools/build_country_index.py --help`-এ সব অপশন আছে।
