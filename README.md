# 🎬 #1 All Live Stream Links — Hourly Action

একটি GitHub Action প্রতি ঘণ্টায় সোর্স প্লেলিস্টের সব স্ট্রিম পরীক্ষা করে **শুধু একটি লাইভ প্লেলিস্ট** তৈরি করে। বাংলা-সহ সব দেশের ও সব ভাষার কাজ করা স্ট্রিম রাখা হয়; দেশ বা ভাষা অনুযায়ী কোনো ফিল্টার নেই।

- **ডুপ্লিকেট মুছে ফেলা হয় না।** একই নাম, একই লিংক, এমনকি একই এন্ট্রি একাধিকবার থাকলেও প্রতিটি লাইভ এন্ট্রি সোর্সের একই ক্রমে রাখা হয়। একই URL অপ্রয়োজনীয় নেটওয়ার্ক লোড কমাতে একবার পরীক্ষা করা হয়।
- মূল `#EXTINF`, প্লেলিস্ট হেডার এবং এন্ট্রির নির্দেশনা সংরক্ষণ করা হয়।
- মূল সোর্স ফাইল বদলানো হয় না, তাই আগে বন্ধ থাকা লিংকও পরের ঘণ্টায় আবার পরীক্ষা হয়।
- কোনো আলাদা প্রিমিয়াম, ডিডুপ্লিকেটেড বা দেশভিত্তিক প্লেলিস্ট তৈরি হয় না।

## লাইভ প্লেলিস্ট

**`playlists/FINAL_ULTIMATE_LIVE_CHECKED.m3u`** — সর্বশেষ সফল চেকে পাওয়া সব লাইভ এন্ট্রি, ডুপ্লিকেটসহ। Action run-এর summary-তে চেক করা ও লাইভ লিংকের সংখ্যা দেখা যায়; এই একটি প্লেলিস্টই সাত দিনের artifact হিসেবেও রাখা হয়।

ডিফল্ট সোর্স হলো `playlists/ULTIMATE_LIVE_5261.m3u`। অন্য সোর্স ব্যবহার করতে `config.yaml`-এর `input.file` বদলান। শুধু কনফিগে নির্বাচিত ফাইল পরীক্ষা হয়; অন্য প্লেলিস্ট স্বয়ংক্রিয়ভাবে যোগ করা হয় না।

## Action চালু করুন

1. পরিবর্তনগুলো রিপোজিটরির **default branch**-এ merge করুন এবং **Actions** সক্রিয় করুন। Scheduled workflow default branch থেকেই চলে।
2. **Settings → Actions → General → Workflow permissions**-এ read/write permission দিন; branch protection থাকলে বটের push অনুমোদন করতে হবে।
3. প্রয়োজনে **Settings → Secrets and variables → Actions**-এ `BD_PROXY` secret যোগ করুন, যেমন `socks5h://user:password@host:port`। শুধু অনুমোদিত proxy ব্যবহার করুন এবং credentials ফাইলে লিখবেন না। Secret না থাকলে সরাসরি চেক হবে; proxy ব্যর্থ হলে ডিফল্টভাবে সরাসরি আবার চেষ্টা হবে।
4. **Actions → #1 All Live Stream Links — Hourly → Run workflow** থেকে হাতে চালাতে পারেন। অন্যথায় `0 * * * *` অনুযায়ী প্রতি ঘণ্টায় UTC সময়ে চালু হবে।

GitHub নির্ধারিত run বিলম্বিত বা বাদ দিতে পারে এবং নিষ্ক্রিয় রিপোজিটরির schedule বন্ধ করতে পারে। একই branch-এ দুটি run একসঙ্গে চলবে না; ৬০ মিনিটের বেশি লাগলে run ব্যর্থ হবে, অসম্পূর্ণ প্লেলিস্ট প্রকাশ হবে না। ঘণ্টায় ঘণ্টায় run করলে GitHub Actions minutes বেশি লাগতে পারে।

## কীভাবে পরীক্ষা হয়

HTTP(S) HLS প্লেলিস্টের media segment এবং সরাসরি স্ট্রিমের অল্প কিছু media data পরীক্ষা করা হয়। সফল মানে চেকের সময় GitHub runner থেকে media পৌঁছানো গেছে; ভিডিও decode, DRM/key বা ভবিষ্যতে playback নিশ্চিত করা হয় না। Geo-block, authentication, rate limit বা নেটওয়ার্ক সমস্যায় কাজ করা লিংকও unreachable দেখা যেতে পারে। Playlist directive সংরক্ষিত থাকে, তবে directive-এ দেওয়া custom player headers HTTP চেকে প্রয়োগ করা হয় না।

ইনপুট না থাকলে, খালি/ভুল হলে, non-HTTP(S) এন্ট্রি থাকলে, চেক অসম্পূর্ণ হলে অথবা **একটিও লাইভ স্ট্রিম যাচাই না হলে** run ব্যর্থ হয় এবং পুরোনো আউটপুট অপরিবর্তিত থাকে। সে ক্ষেত্রে আগের প্লেলিস্টটি পুরোনো হতে পারে; Action logs দেখুন। প্রতিটি URL-এর আগে `#EXTINF` থাকতে হবে।

## কনফিগ ও লোকাল টেস্ট

```yaml
input:
  file: "playlists/ULTIMATE_LIVE_5261.m3u"
  url: ""                   # ফাইল না থাকলে ঐচ্ছিক download URL
output:
  final_checked: "playlists/FINAL_ULTIMATE_LIVE_CHECKED.m3u"
checker:
  timeout: 8                # প্রতি প্রচেষ্টার সময়সীমা, সেকেন্ডে
  workers: 50               # সমান্তরাল চেক, proxy fallback-সহ
  retries: 1
  deep_check: true          # HLS media segment-ও পরীক্ষা করে
  proxy: "${BD_PROXY}"
  fallback_direct: true
```

Python 3.11 ও `curl` প্রয়োজন। Action-এর artifact ও commit path ডিফল্ট আউটপুটের জন্য নির্ধারিত; আউটপুটের path বদলালে workflow-টিও বদলাতে হবে।

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
python src/main.py
```

টেস্টগুলো স্থানীয় HTTP fixture ব্যবহার করে; আসল স্ট্রিম সার্ভারে যোগাযোগ করে না। শুধু নিজের বা ব্যবহারের অনুমতি আছে এমন স্ট্রিম ও proxy পরীক্ষা করুন।
