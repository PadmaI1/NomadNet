#!/usr/bin/env python3
"""
Generates seed_data.sql for NomadNet: 20 users, 14 locations, ~100 posts
(with Unsplash media), likes, comments, and follow graphs.

Run: python3 generate_seed_data.py
Then: python3 load_seed_data.py
"""

import random
from datetime import datetime, timedelta

random.seed(42)

# A fixed, pre-computed werkzeug scrypt hash for the shared test password
# "NomadNet2026!" so every seed account can actually log in.
PASSWORD_HASH = "scrypt:32768:8:1$JhBq1sULwXwkv7qE$39e7022a4c59fa5958bf77180460a01ba0d80e941d0054281c39ed3ac7fadf6b45f33d4da2b3fd8c796cf41550e39a1dd385357701614f9fdb65efba24721bb0"

PORTRAITS = [
    "1507003211169-0a1dd7228f2d", "1494790108377-be9c29b29330", "1500648767791-00dcc994a43e",
    "1438761681033-6461ffad8d80", "1544005313-94ddf0286df2", "1517841905240-472988babdf9",
    "1524504388940-b1c1722653e1", "1506794778202-cad84cf45f1d", "1519345182560-3f2917c472ef",
    "1522075469751-3a6694fb2f61", "1531123897727-8f129e1688ce", "1552058544-f2b08422138a",
    "1546456073-92b9f0a8d413", "1492562080023-ab3db95bfbce", "1489980557514-251d61e3eeb6",
    "1487412720507-e7ab37603c6f", "1508214751196-bcfd4ca60f91", "1544723795-3fb6469f5b39",
    "1573497019940-1c28c88b4f3e", "1524250502761-1ac6f2e30d43",
]

TRAVEL = [
    "1506905925346-21bda4d32df4", "1480714378408-67cf0d13bc1b", "1507525428034-b723cf961d3e",
    "1493976040374-85c8e12f0c0e", "1519677100203-a0e668c92439", "1528181304800-259b08848526",
    "1533105079780-92b9be482077", "1476514525535-07fb3b4ae5f1", "1523906834658-6e24ef2386f9",
    "1523482580672-f109ba8cb9be", "1512100356356-de1b84283e18", "1502920917128-1aa500764cbd",
    "1500835556837-99ac94a94552", "1548013146-72479768bada", "1541480601022-2308c0f02487",
    "1518548419970-58e3b4079ab2", "1571003123894-1f0594d2b5d9", "1516483638261-f4dbaf036963",
    "1483729558449-99ef09a8c325", "1530521954074-e64f6810b32d",
]


def avatar(i):
    return f"https://images.unsplash.com/photo-{PORTRAITS[i % len(PORTRAITS)]}?w=256&h=256&fit=crop&q=80"


def photo(i, w=1200):
    return f"https://images.unsplash.com/photo-{TRAVEL[i % len(TRAVEL)]}?w={w}&q=80"


def esc(s):
    return s.replace("'", "''")


NOW = datetime(2026, 9, 21, 12, 0, 0)


def days_ago(d, hours=0):
    dt = NOW - timedelta(days=d, hours=hours)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# USERS
# ---------------------------------------------------------------------------
USERS = [
    ("alex_explorer", "alex@example.com", "Digital nomad exploring Southeast Asia. Coffee-powered, wifi-dependent. \U0001F30F", True),
    ("luna_traveler", "luna@example.com", "Photography & travel enthusiast. Chasing golden hour across three continents. ✈️", False),
    ("marco_nomad", "marco@example.com", "Remote backend engineer. Coffee snob, mountain lover. ☕", True),
    ("jasmine_adventure", "jasmine@example.com", "Adventure seeker & nature lover. Currently based between Bali and Chiang Mai. \U0001F3D4️", False),
    ("kai_island", "kai@example.com", "Beach bum, island hopper, freelance designer. \U0001F3DD️", False),
    ("elena_vance", "elena.vance@example.com", "Slow travel advocate. Field notes from wherever the wifi is fast. \U0001F4F6", True),
    ("marcus_reyes", "marcus.reyes@example.com", "Remote sound engineer chasing quiet corners of the world. \U0001F3A7", False),
    ("hilda_novak", "hilda.novak@example.com", "Landscape photographer. Currently chasing alpine light in Switzerland. \U0001F4F7", True),
    ("priya_desai", "priya.desai@example.com", "Product manager working async from co-working spaces worldwide. \U0001F4BB", False),
    ("tomas_silva", "tomas.silva@example.com", "Surf instructor turned remote copywriter. Portugal born, world raised. \U0001F30A", False),
    ("sofia_martins", "sofia.martins@example.com", "UX researcher. Slow mornings, fast wifi, good coffee. ☕", True),
    ("daniel_kim", "daniel.kim@example.com", "Full-stack dev bouncing between Seoul, Kyoto and Bangkok. \U0001F468‍\U0001F4BB", False),
    ("amara_okafor", "amara.okafor@example.com", "Travel writer documenting nomad hubs across Asia and Latin America. ✍️", True),
    ("felix_bauer", "felix.bauer@example.com", "Data engineer, mountain hiker, amateur baker. \U0001F9C1", False),
    ("nina_petrova", "nina.petrova@example.com", "Freelance illustrator sketching every city she lands in. \U0001F3A8", False),
    ("ravi_kumar", "ravi.kumar@example.com", "DevOps engineer, forever chasing 24°C and reliable fiber. \U0001F310", False),
    ("camila_torres", "camila.torres@example.com", "Yoga teacher & wellness coach. Currently in Oaxaca. \U0001F9D8", False),
    ("liam_oconnor", "liam.oconnor@example.com", "Indie game dev working from a different timezone every month. \U0001F3AE", False),
    ("yuki_tanaka", "yuki.tanaka@example.com", "Architecture photographer based between Kyoto and Barcelona. \U0001F3EF", True),
    ("zara_ahmed", "zara.ahmed@example.com", "Community manager for a remote-first startup. Beach mornings, laptop afternoons. \U0001F334", False),
]

# ---------------------------------------------------------------------------
# COUNTRIES
# ---------------------------------------------------------------------------
COUNTRIES = [
    ("Indonesia", "ID"), ("Thailand", "TH"), ("Vietnam", "VN"), ("Japan", "JP"),
    ("Portugal", "PT"), ("Switzerland", "CH"), ("Mexico", "MX"), ("Spain", "ES"),
]

# ---------------------------------------------------------------------------
# LOCATIONS: (name, type, emoji, country, city, lat, lon, photo_idx, description)
# ---------------------------------------------------------------------------
LOCATIONS = [
    ("Bali", "island", "\U0001F3DD️", "Indonesia", "Denpasar", -8.6500, 115.2167, 0,
     "Bali, Indonesia — Tropical paradise with pristine beaches, terraced rice fields, and vibrant culture. Perfect for digital nomads seeking warm weather and affordable living."),
    ("Bangkok", "city", "\U0001F3D9️", "Thailand", "Bangkok", 13.7563, 100.5018, 1,
     "Bangkok, Thailand — Bustling metropolis with legendary street food, ornate temples, and an endless supply of co-working spaces."),
    ("Chiang Mai", "mountain", "⛰️", "Thailand", "Chiang Mai", 18.7883, 98.9853, 2,
     "Chiang Mai, Thailand — Mountain views, affordable living, and one of the strongest digital nomad communities in Asia."),
    ("Phuket", "beach", "\U0001F3D6️", "Thailand", "Phuket", 7.9519, 98.3387, 3,
     "Phuket, Thailand — Sandy beaches, water sports, and a vibrant nightlife scene for travelers who want to unwind."),
    ("Kyoto", "temple", "⛩️", "Japan", "Kyoto", 35.0116, 135.7681, 4,
     "Kyoto, Japan — Centuries-old temples, bamboo groves, and quiet Machiya cafes ideal for focused remote work."),
    ("Ubud", "village", "\U0001F3D8️", "Indonesia", "Ubud", -8.5069, 115.2625, 5,
     "Ubud, Indonesia — Jungle village at the heart of Bali, known for yoga retreats, rice paddies, and a thriving wellness scene."),
    ("Hoi An", "village", "\U0001F3EE", "Vietnam", "Hoi An", 15.8801, 108.3380, 6,
     "Hoi An, Vietnam — Lantern-lit ancient town with tailor shops, river cafes, and an easy pace of life."),
    ("Da Lat", "forest", "\U0001F332", "Vietnam", "Da Lat", 11.9404, 108.4583, 7,
     "Da Lat, Vietnam — Pine forests and cool mountain air in Vietnam's Central Highlands, a favorite for quiet writing retreats."),
    ("Lisbon", "cafe", "☕", "Portugal", "Lisbon", 38.7223, -9.1393, 8,
     "Lisbon, Portugal — Hillside streets, azulejo tiles, and a booming co-working scene overlooking the Tagus river."),
    ("Porto", "city", "\U0001F3D9️", "Portugal", "Porto", 41.1579, -8.6291, 9,
     "Porto, Portugal — Riverside charm, port wine cellars, and a growing cluster of nomad-friendly cafes."),
    ("Lauterbrunnen", "mountain", "⛰️", "Switzerland", "Lauterbrunnen", 46.5934, 7.9081, 10,
     "Lauterbrunnen, Switzerland — A valley of 72 waterfalls beneath the Bernese Alps, with alpine chalets built for deep focus."),
    ("Interlaken", "nature", "\U0001F3D4️", "Switzerland", "Interlaken", 46.6863, 7.8632, 11,
     "Interlaken, Switzerland — Nestled between two lakes with panoramic views of the Jungfrau massif."),
    ("Oaxaca", "village", "\U0001F3D8️", "Mexico", "Oaxaca", 17.0732, -96.7266, 12,
     "Oaxaca, Mexico — Colorful colonial streets, legendary food markets, and a laid-back creative community."),
    ("Barcelona", "city", "\U0001F3D9️", "Spain", "Barcelona", 41.3874, 2.1686, 13,
     "Barcelona, Spain — Gaudi architecture, beachfront co-working, and one of Europe's largest nomad communities."),
]

POST_TEMPLATES = [
    "Found this incredible spot in {name} today — the {type} views are unreal and the wifi actually holds up for video calls. Already planning to extend my stay.",
    "Three weeks into {city} and I still haven't gotten tired of the mornings here. Slow coffee, then a few hours of deep work before the heat kicks in.",
    "If you're a remote worker heading to {name}, book somewhere with a balcony. The sunrise over the {type} is worth the early alarm.",
    "Met a handful of fellow nomads at a co-working space in {city} today. Swapped notes on visas, fast SIM cards, and the best noodle stalls nearby.",
    "Rainy day in {name}, so I finally caught up on a backlog of code review from a quiet cafe corner. Sometimes the slow days are the best ones.",
    "Six months of full-time travel and {city} might be my favorite base so far — cheap, fast internet, and genuinely kind people.",
    "Hiked out to the edge of town in {name} this morning before starting work. Nothing clears your head like a walk through a {type} landscape.",
    "Quick PSA for anyone passing through {city}: the local market opens at dawn and the produce is unbeatable. Perfect fuel for a long coding session.",
    "Wrapped up a big project this week from a rooftop workspace in {name}. The view of the {type} made every deadline feel a little less stressful.",
    "Two nomads, one shared apartment, and a surprisingly reliable fiber connection in {city}. This is exactly the kind of setup I came looking for.",
]

COMMENT_TEMPLATES = [
    "This looks amazing! Adding it to my list \U0001F64C",
    "How's the wifi speed there? Planning a trip next month.",
    "I was just here last year, still think about the food constantly.",
    "Okay this settles it, booking a flight tonight \U0001F602",
    "Love this shot. What camera are you using?",
    "Any recommendations for a good co-working space nearby?",
    "The light in this photo is incredible.",
    "Following your trip closely, take me with you next time!",
    "Is it very crowded this time of year?",
    "This is exactly the kind of content I follow this app for.",
    "Saving this for when I finally book that trip.",
    "How long are you staying there for?",
]


def build():
    lines = []
    lines.append("-- NomadNet Seed Data")
    lines.append("-- Auto-generated by generate_seed_data.py")
    lines.append("-- 20 users, 14 locations, posts/likes/comments/follows with Unsplash media")
    lines.append("-- Shared test password for every seeded account: NomadNet2026!")
    lines.append("")

    # USERS
    lines.append("-- ============================================================================")
    lines.append("-- USERS")
    lines.append("-- ============================================================================")
    lines.append("INSERT INTO user (id, username, email, password, created_at, avatar_url, bio, is_verified) VALUES")
    user_rows = []
    for i, (uname, email, bio, verified) in enumerate(USERS, start=1):
        created = days_ago(random.randint(10, 400))
        user_rows.append(
            f"({i}, '{esc(uname)}', '{esc(email)}', '{PASSWORD_HASH}', '{created}', "
            f"'{avatar(i - 1)}', '{esc(bio)}', {1 if verified else 0})"
        )
    lines.append(",\n".join(user_rows) + ";")
    lines.append("")

    # COUNTRIES
    lines.append("-- ============================================================================")
    lines.append("-- COUNTRIES")
    lines.append("-- ============================================================================")
    lines.append("INSERT INTO country (id, name, code) VALUES")
    country_rows = [f"({i}, '{esc(n)}', '{c}')" for i, (n, c) in enumerate(COUNTRIES, start=1)]
    lines.append(",\n".join(country_rows) + ";")
    lines.append("")

    # LOCATIONS
    lines.append("-- ============================================================================")
    lines.append("-- LOCATIONS")
    lines.append("-- ============================================================================")
    lines.append(
        "INSERT INTO location (id, name, type, country, city, latitude, longitude, provider, "
        "provider_id, hero_image_url, description, rating, emoji, is_verified) VALUES"
    )
    loc_rows = []
    for i, (name, ltype, emoji, country, city, lat, lon, pidx, desc) in enumerate(LOCATIONS, start=1):
        verified = 1 if i % 2 == 0 else 0
        loc_rows.append(
            f"({i}, '{esc(name)}', '{ltype}', '{esc(country)}', '{esc(city)}', {lat}, {lon}, "
            f"'openstreetmap', '{100000 + i}', '{photo(pidx, 1200)}', '{esc(desc)}', 0.0, '{emoji}', {verified})"
        )
    lines.append(",\n".join(loc_rows) + ";")
    lines.append("")

    # POSTS + MEDIA
    lines.append("-- ============================================================================")
    lines.append("-- POSTS")
    lines.append("-- ============================================================================")
    post_rows = []
    media_rows = []
    post_id = 1
    media_id = 1
    post_meta = []  # (post_id, location_idx)
    for loc_idx, (name, ltype, emoji, country, city, lat, lon, pidx, desc) in enumerate(LOCATIONS, start=1):
        num_posts = random.randint(6, 9)
        for _ in range(num_posts):
            author = random.randint(1, len(USERS))
            template = random.choice(POST_TEMPLATES)
            content = template.format(name=name, type=ltype, city=city)
            created_days = random.randint(0, 28)
            created_hours = random.randint(0, 23)
            created = days_ago(created_days, created_hours)
            post_rows.append(
                f"({post_id}, '{esc(content)}', '{created}', {author}, {loc_idx})"
            )
            n_media = random.choice([1, 1, 1, 2])
            for m in range(n_media):
                media_rows.append(
                    f"({media_id}, {post_id}, '{photo((pidx + m + 1))}', 'image', {m}, '{created}')"
                )
                media_id += 1
            post_meta.append(post_id)
            post_id += 1
    lines.append("INSERT INTO post (id, content, created_at, user_id, location_id) VALUES")
    lines.append(",\n".join(post_rows) + ";")
    lines.append("")
    lines.append("-- ============================================================================")
    lines.append("-- POST MEDIA")
    lines.append("-- ============================================================================")
    lines.append("INSERT INTO post_media (id, post_id, filename, media_type, display_order, created_at) VALUES")
    lines.append(",\n".join(media_rows) + ";")
    lines.append("")

    # LIKES
    lines.append("-- ============================================================================")
    lines.append("-- LIKES")
    lines.append("-- ============================================================================")
    like_rows = []
    like_id = 1
    for pid in post_meta:
        n_likes = random.randint(2, 14)
        likers = random.sample(range(1, len(USERS) + 1), min(n_likes, len(USERS)))
        for uid in likers:
            created = days_ago(random.randint(0, 27))
            like_rows.append(f"({like_id}, {uid}, {pid}, '{created}')")
            like_id += 1
    lines.append("INSERT INTO like (id, user_id, post_id, created_at) VALUES")
    lines.append(",\n".join(like_rows) + ";")
    lines.append("")

    # COMMENTS
    lines.append("-- ============================================================================")
    lines.append("-- COMMENTS")
    lines.append("-- ============================================================================")
    comment_rows = []
    comment_id = 1
    for pid in post_meta:
        n_comments = random.randint(0, 5)
        for _ in range(n_comments):
            uid = random.randint(1, len(USERS))
            text = random.choice(COMMENT_TEMPLATES)
            created = days_ago(random.randint(0, 27))
            comment_rows.append(f"({comment_id}, '{esc(text)}', '{created}', {uid}, {pid})")
            comment_id += 1
    lines.append("INSERT INTO comment (id, content, created_at, user_id, post_id) VALUES")
    lines.append(",\n".join(comment_rows) + ";")
    lines.append("")

    # FOLLOWS (user -> user)
    lines.append("-- ============================================================================")
    lines.append("-- USER FOLLOWS")
    lines.append("-- ============================================================================")
    follow_rows = []
    follow_id = 1
    seen_pairs = set()
    for uid in range(1, len(USERS) + 1):
        n_follows = random.randint(3, 7)
        candidates = [u for u in range(1, len(USERS) + 1) if u != uid]
        for followed in random.sample(candidates, min(n_follows, len(candidates))):
            if (uid, followed) in seen_pairs:
                continue
            seen_pairs.add((uid, followed))
            created = days_ago(random.randint(5, 300))
            follow_rows.append(f"({follow_id}, {uid}, {followed}, '{created}')")
            follow_id += 1
    lines.append("INSERT INTO follow (id, follower_id, followed_id, created_at) VALUES")
    lines.append(",\n".join(follow_rows) + ";")
    lines.append("")

    # LOCATION FOLLOWS
    lines.append("-- ============================================================================")
    lines.append("-- LOCATION FOLLOWS")
    lines.append("-- ============================================================================")
    lf_rows = []
    lf_id = 1
    seen_lf = set()
    for uid in range(1, len(USERS) + 1):
        n_follows = random.randint(2, 6)
        for loc_id in random.sample(range(1, len(LOCATIONS) + 1), min(n_follows, len(LOCATIONS))):
            if (uid, loc_id) in seen_lf:
                continue
            seen_lf.add((uid, loc_id))
            lf_rows.append(f"({lf_id}, {uid}, {loc_id})")
            lf_id += 1
    lines.append("INSERT INTO location_follow (id, user_id, location_id) VALUES")
    lines.append(",\n".join(lf_rows) + ";")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    sql = build()
    with open("seed_data.sql", "w") as f:
        f.write(sql)
    print(f"Wrote seed_data.sql ({len(sql)} bytes)")
