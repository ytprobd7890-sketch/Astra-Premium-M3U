# 🌍 #1 Live Stream Links — Hourly Action + Server-IP Country Split

একটি GitHub Action প্রতি ঘণ্টায় সোর্স প্লেলিস্টের সব স্ট্রিম পরীক্ষা করে **যাচাই করা লাইভ এন্ট্রি** প্রকাশ করে — এবং প্রতিটি সার্ভারের IP কোন দেশে, সেই অনুযায়ী আলাদা প্লেলিস্ট বানায়। বাংলা-সহ সব দেশ ও ভাষার কাজ করা স্ট্রিম রাখা হয়।

## যা তৈরি হয়

| ফাইল | কী থাকে |
| --- | --- |
| `playlists/FINAL_ULTIMATE_LIVE_CHECKED.m3u` | সব যাচাই করা লাইভ এন্ট্রি, ডুপ্লিকেটসহ, সোর্সের ক্রমে |
| `playlists/by_country/COUNTRY_MASTER.m3u` | একই লাইভ এন্ট্রি, দেশ অনুযায়ী গ্রুপ করা (একটি মাস্টার ফাইল) |
| `playlists/by_country/<CODE>_<COUNTRY>.m3u` | প্রতিটি সার্ভার-দেশের আলাদা ফাইল, যেমন `BD_BANGLADESH.m3u`, `PK_PAKISTAN.m3u` |
| `playlists/by_country/XX_UNKNOWN.m3u` | যে সার্ভার IP-র দেশ বোঝা যায়নি (প্রাইভেট/রিজার্ভড/DNS ব্যর্থ) |

**দেশ মানে চ্যানেলের দেশ নয়, সার্ভারের দেশ।** প্লেলিস্টে যেসব IP থাকে (যেমন `103.253.18.58:8000`), সেগুলোর ভৌগোলিক অবস্থানই গ্রুপিংয়ের ভিত্তি। এতে বোঝা যায় আপনার লাইভ লিস্ট আসলে কোন দেশের সার্ভারের ওপর নির্ভর করছে।

উদাহরণ — এই রিপোর সর্বশেষ চেকে (২০১৭টি লাইভ এন্ট্রি, ৬৫টি সার্ভার IP):

| গ্রুপ | সার্ভার | লাইভ এন্ট্রি |
| --- | ---: | ---: |
| 🇨🇴 কলম্বিয়া (CO) | 6 | 503 |
| 🇪🇨 ইকুয়েডর (EC) | 4 | 443 |
| 🇵🇰 পাকিস্তান (PK) | 8 | 340 |
| 🇵🇪 পেরু (PE) | 3 | 242 |
| 🇩🇴 ডোমিনিকান প্রজাতন্ত্র (DO) | 1 | 146 |
| 🇬🇹 গুয়াতেমালা (GT) | 1 | 112 |
| 🇧🇩 বাংলাদেশ (BD) | 2 | 108 |
| 🇵🇾 প্যারাগুয়ে (PY) | 1 | 70 |
| 🇭🇳 হন্ডুরাস (HN) | 2 | 42 |
| 🇵🇹 পর্তুগাল (PT) | 1 | 11 |

প্রতিটি ফাইলের হেডারে থাকে `# Astra server country: ...` এবং `#EXTINF`-এ:

```m3u
#EXTINF:-1 group-title="🇧🇩 বাংলাদেশ (BD)" tvg-country="BD",Channel Name
#EXTGRP:🇧🇩 বাংলাদেশ (BD)
http://203.0.113.10:8000/play/a001
```

- `group-title` বাংলা-প্রথম দেশের নাম দিয়ে লেখা; পুরোনো `group-title` বদলে যায়, চ্যানেলের নাম/`tvg-name`/`tvg-id`/অন্য attribute অপরিবর্তিত থাকে।
- `#EXTGRP` যোগ করা হয় শুধুযখন সোর্সে আগে থেকে না থাকে — যে প্লেয়ার `group-title` পড়ে না, সেটিও গ্রুপ দেখায়।
- দেশের ক্রম: বাংলাদেশ প্রথমে, তারপর বাংলা বর্ণানুক্রম, শেষে অজানা সার্ভার।

## ডুপ্লিকেট ও ক্রম

- **ডুপ্লিকেট মুছে ফেলা হয় না।** একই নাম, একই লিংক, এমনকি হুবহু একই এন্ট্রি একাধিকবার থাকলে প্রতিটি লাইভ এন্ট্রি সোর্সের ক্রমেই থাকে।
- একই URL-এর জন্য নেটওয়ার্ক লোড কমাতে একবার পরীক্ষা হয়, কিন্তু লেখার সময় প্রতিটি এন্ট্রি আলাদা থাকে।
- মূল `#EXTINF`, প্লেলিস্ট হেডার ও এন্ট্রির নির্দেশনা সংরক্ষিত থাকে; শুধু দেশ-সংক্রান্ত attribute বদলায়।
- মূল সোর্স ফাইল কখনো বদলানো হয় না, তাই আগে বন্ধ থাকা লিংক পরের ঘণ্টায় আবার পরীক্ষা হয়।

## Action চালু করুন

1. পরিবর্তনগুলো রিপোজিটরির **default branch**-এ merge করুন এবং **Actions** সক্রিয় করুন। Scheduled workflow default branch থেকেই চলে।
2. **Settings → Actions → General → Workflow permissions**-এ read/write permission দিন; branch protection থাকলে বটের push অনুমোদন করতে হবে।
3. প্রয়োজনে **Settings → Secrets and variables → Actions**-এ `BD_PROXY` secret যোগ করুন, যেমন `socks5h://user:password@host:port`। শুধু অনুমোদিত proxy ব্যবহার করুন এবং credentials ফাইলে লিখবেন না। Secret না থাকলে সরাসরি চেক হবে; proxy ব্যর্থ হলে ডিফল্টভাবে সরাসরি আবার চেষ্টা হবে।
4. **Actions → 🤖 #1 All Live Stream Links — Hourly → Run workflow** থেকে হাতে চালাতে পারেন। অন্যথায় `0 * * * *` অনুযায়ী প্রতি ঘণ্টায় UTC সময়ে চালু হবে।

GitHub নির্ধারিত run বিলম্বিত বা বাদ দিতে পারে এবং নিষ্ক্রিয় রিপোজিটরির schedule বন্ধ করতে পারে। একই branch-এ দুটি run একসঙ্গে চলবে না; ৬০ মিনিটের বেশি লাগলে run ব্যর্থ হবে, অসম্পূর্ণ প্লেলিস্ট প্রকাশ হবে না। ঘণ্টায় ঘণ্টায় run করলে GitHub Actions minutes বেশি লাগতে পারে।

## দেশ ঠিক করা হয় কীভাবে

- **সম্পূর্ণ অফলাইন**: চেক করা প্রতিটি লাইভ URL-এর হোস্ট নেওয়া হয়; হোস্টনেম হলে DNS দিয়ে IP পাওয়া হয়; তারপর `src/data/`-এর DB-IP সূচিতে বাইনারি সার্চ।
- IPv4 ও IPv6 দুটোই সমর্থিত। প্রাইভেট/রিজার্ভড ঠিকানা (RFC1918, loopback, link-local, CGNAT, multicast) কখনো কোনো দেশে যায় না।
- DNS ব্যর্থ হলে বা ঠিকানা সূচিতে না থাকলে এন্ট্রি `XX_UNKNOWN.m3u`-তে যায় — অনুমান করা হয় না।
- করা হয় না: কোনো অনলাইন API, কোনো API key, কোনো রেট লিমিট।

## কীভাবে পরীক্ষা হয়

HTTP(S) HLS প্লেলিস্টের media segment এবং সরাসরি স্ট্রিমের অল্প কিছু media data পরীক্ষা করা হয়। সফল মানে চেকের সময় GitHub runner থেকে media পৌঁছানো গেছে; ভিডিও decode, DRM/key বা ভবিষ্যতে playback নিশ্চিত করা হয় না। Geo-block, authentication, rate limit বা নেটওয়ার্ক সমস্যায় কাজ করা লিংকও unreachable দেখা যেতে পারে। Playlist directive সংরক্ষিত থাকে, তবে directive-এ দেওয়া custom player headers HTTP চেকে প্রয়োগ করা হয় না।

ইনপুট না থাকলে, খালি/ভুল হলে, non-HTTP(S) এন্ট্রি থাকলে, চেক অসম্পূর্ণ হলে অথবা **একটিও লাইভ স্ট্রিম যাচাই না হলে** run ব্যর্থ হয় এবং পুরোনো আউটপুট অপরিবর্তিত থাকে। সে ক্ষেত্রে আগের প্লেলিস্টটি পুরোনো হতে পারে; Action logs দেখুন। প্রতিটি URL-এর আগে `#EXTINF` থাকতে হবে।

## কনফিগ

```yaml
input:
  file: "playlists/ULTIMATE_LIVE_5261.m3u"
  url: ""                        # ফাইল না থাকলে ঐচ্ছিক download URL
output:
  final_checked: "playlists/FINAL_ULTIMATE_LIVE_CHECKED.m3u"
  by_server_country: "playlists/by_country"   # মাস্টার + দেশভিত্তিক ফাইল
  countries: true                # false করলে শুধু final_checked লেখা হয়
checker:
  timeout: 8                     # প্রতি প্রচেষ্টার সময়সীমা, সেকেন্ডে
  workers: 50                    # সমান্তরাল চেক, proxy fallback-সহ
  retries: 1
  deep_check: true               # HLS media segment-ও পরীক্ষা করে
  proxy: "${BD_PROXY}"
  fallback_direct: true
```

ডিফল্ট সোর্স `playlists/ULTIMATE_LIVE_5261.m3u`। অন্য সোর্স ব্যবহার করতে `input.file` বদলান। শুধু কনফিগে নির্বাচিত ফাইল পরীক্ষা হয়; অন্য প্লেলিস্ট স্বয়ংক্রিয়ভাবে যোগ করা হয় না।

## লোকাল টেস্ট

Python 3.11 ও `curl` প্রয়োজন।

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
python src/main.py
```

টেস্টগুলো স্থানীয় HTTP fixture ব্যবহার করে; আসল স্ট্রিম সার্ভারে যোগাযোগ করে না। শুধু নিজের বা ব্যবহারের অনুমতি আছে এমন স্ট্রিম ও proxy পরীক্ষা করুন।

## ফাইল কাঠামো

```
src/main.py                 চেক → লাইভ ফিল্টার → দেশভিত্তিক পাবলিশ
src/checker.py              curl-ভিত্তিক সমান্তরাল স্ট্রিম চেক
src/utils.py                M3U পার্সিং, ডুপ্লিকেট অক্ষুণ্ণ
src/geoip.py                অফলাইন IP → দেশ লুকআপ (DNS+LPM)
src/splitter.py             দেশভিত্তিক গ্রুপিং ও প্লেলিস্ট লেখা
src/countries.py            ISO কোড, বাংলা নাম, পতাকা, বাংলা বর্ণক্রম
src/data/                   DB-IP সূচি (CC BY 4.0, NOTICE.md দেখুন)
tools/build_country_index.py   সূচি নতুন করে বানানোর স্ক্রিপ্ট
```

## অ্যাট্রিবিউশন

সার্ভার-দেশ ডেটা **DB-IP IP to Country Lite** থেকে, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) লাইসেন্সে; [sapics/ip-location-db](https://github.com/sapics/ip-location-db)-এর মাধ্যমে পুনঃপ্রকাশিত। বিস্তারিত `src/data/NOTICE.md`-এ।

> IP Geolocation by [DB-IP](https://db-ip.com)
