# 🎬 Phantom Inspiration Studio — API Setup Guide

This guide walks you through exactly which websites you need to create accounts on, what to do on each, and how to get the API keys/credentials needed to upload videos and earn money.

---

## 📋 Quick Overview

| Platform | Account Needed | API Cost | Earn Money? | Difficulty |
|----------|---------------|----------|-------------|------------|
| **YouTube** | Google Account | Free | ✅ AdSense | ⭐⭐ |
| **TikTok** | TikTok Developer | Free | ✅ Creator Rewards | ⭐⭐ |
| **Instagram** | Facebook Developer | Free | ✅ Bonuses/Reels | ⭐⭐⭐ |
| **X / Twitter** | X Developer | Free | ✅ Ad Revenue | ⭐⭐ |
| **Rumble** | Rumble Account | Free | ✅ Ad Revenue | ⭐ |
| **Facebook** | Facebook Developer | Free | ✅ In-stream ads | ⭐⭐⭐ |
| **Snapchat** | Snap Developer | Free | ✅ Spotlight | ⭐⭐⭐ |
| **Pinterest** | Pinterest Developer | Free | ✅ Idea Pins | ⭐⭐ |

----

## 1️⃣ YouTube (Best for long-term revenue)

**Website:** https://console.cloud.google.com

### Steps:
1. **Create a Google Account** if you don't have one
2. Go to **Google Cloud Console** → Create a **New Project**
3. Search for **"YouTube Data API v3"** → **Enable** it
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Application type: **Desktop app**
6. Download the JSON file → rename to `youtube_client_secret.json`
7. Place it in: `config/youtube_client_secret.json`

### To earn money:
- Go to https://studio.youtube.com → **Monetization** tab
- Requirements: **1,000 subscribers** + **4,000 watch hours** (or 10M Shorts views)
- Link your **AdSense** account — **AdSense is 100% FREE**, no payment needed

### 📺 How to set up AdSense (step by step):

> **Note:** You can only do this AFTER you hit 1,000 subs + 4,000 hours on YouTube.
> But here's exactly what to expect so you're ready:

1. **Go to YouTube Studio** → https://studio.youtube.com
2. Click **"Monetization"** in the left sidebar
3. Click **"Start"** to begin the application
4. **Sign in to AdSense** with the same Google account
   - If you don't have an AdSense account yet, it will create one for you
5. **Fill in your details:**
   - **Legal name** — must match your tax info exactly
   - **Address** — where you live (for tax purposes)
   - **Phone number** — for verification
6. **Select your payment method:**
   - **Bank account** (direct deposit) — fastest, free
   - Or **wire transfer** / **check by mail** (slower)
7. **Submit your tax info** (W-9 for US, equivalent for your country)
   - AdSense will ask: are you a US person for tax purposes?
   - Answer honestly — this determines tax withholding
8. **Wait for approval** — Google reviews your channel (usually 1–2 weeks)
9. **Once approved:**
   - Ads automatically appear on your videos
   - You earn money when viewers watch or click ads
   - **Payout threshold:** $100 USD minimum before they send you money
   - Payments go out around the **21st of each month**

### 💡 AdSense tips for new creators:
- **Don't buy fake subs/watch time** — Google will ban you permanently
- **Enable all ad formats** (skippable, non-skippable, overlay, display) to maximize earnings
- **YouTube Shorts** pay less per view than long-form videos
- **Niche matters:** Finance/tech videos earn more per view than entertainment
- **No cost ever** — AdSense never charges you a fee, they just take a cut of ad revenue

### File structure:
```
config/
  youtube_client_secret.json   ← Place this file here
```

---

## 2️⃣ TikTok (Best for viral reach)

**Website:** https://developers.tiktok.com

### Steps:
1. Create a **TikTok Developer Account** (free)
2. Click **"Create App"**
3. Fill in app details (name: "Phantom Studio" or anything)
4. Enable **"Content Posting API"** scope
5. Note your **Client Key** and **Client Secret**
6. Create file: `config/tiktok_credentials.json`

### File content:
```json
{
  "client_key": "YOUR_TIKTOK_CLIENT_KEY",
  "client_secret": "YOUR_TIKTOK_CLIENT_SECRET"
}
```

### To earn money:
- Go to https://www.tiktok.com/creator-rewards
- Requirements: **10,000 followers** + **100,000 video views in 30 days**
- Payout: $0.02–$0.05 per 1,000 views

---

## 3️⃣ Instagram + Facebook (Meta Graph API)

**Website:** https://developers.facebook.com

### ⚠️ IMPORTANT: Create the app under your FACEBOOK account, NOT Instagram

Instagram Graph API **requires** a Facebook Page linked to an Instagram Business/Creator account. You **cannot** create an Instagram-only app. Always create under the Facebook account that owns your Page.

---

### Part A: Instagram Account Setup (one-time, do this FIRST)

Before creating the developer app, your Instagram account must be a **Business** or **Creator** account linked to your Facebook Page:

1. Open the **Instagram app** on your phone
2. Go to **Settings** → **Account** → **Switch to Professional Account**
3. Choose **Creator** (or Business if you have a company)
4. Pick a category (e.g., "Digital Creator")
5. **Link to your Facebook Page** — this is critical:
   - Go to **Settings** → **Business** (or **Creator**) → **Connect a Facebook Page**
   - Select your **PhantomInspiration** Page
6. Verify it's connected: your Instagram profile should show the Page name under "Also managed by"

> **If you skip this step, nothing below will work.** The API rejects non-business accounts.

---

### Part B: Create the Developer App

1. Go to https://developers.facebook.com/apps/creation/
2. **Log in with your Facebook account** (the one that owns the PhantomInspiration Page)
3. **App name:** "Phantom Inspiration Studio" (or anything)
4. **App contact email:** your email
5. Click **Create App**

### Part C: Select Use Cases

You'll see the "Add use cases" screen. Select these **two**:

| Use Case | Why |
|----------|-----|
| ✅ **Manage everything on your Page** | Uploads Reels/videos to your Facebook Page |
| ✅ **Manage messaging & content on Instagram** | Uploads Reels to Instagram |

Click **Next** after selecting both.

### Part D: Add Products

After app creation, you'll be on the app dashboard. Add **both products**:

1. Click **"Add Products to Your App"**
2. Search and add **"Instagram Graph API"** → click **Set Up**
3. Go back, search and add **"Facebook Pages API"** → click **Set Up**

### Part E: Get Permissions (Scopes)

Go to **App Review** → **Permissions and Features**:

Request these permissions:

| Permission | What it does |
|------------|-------------|
| `pages_show_list` | See your Pages |
| `pages_read_engagement` | Read Page data |
| `pages_manage_posts` | Post videos to Facebook Page |
| `instagram_basic` | Read Instagram account info |
| `instagram_content_publish` | Publish Reels to Instagram |

> **Note:** Some permissions are auto-approved for development mode. `instagram_content_publish` requires app review for production.

### Part F: Development Mode (Quick Start — No Review Needed Yet)

While your app is in **Development Mode**:

1. Go to **Roles** → **Roles**
2. Add yourself as **Admin**
3. Your app can now publish to Pages/Instagram accounts you manage
4. Switch to **Live** mode only after app review

### Part G: Get Your Page Access Token

1. Go to https://developers.facebook.com/tools/explorer/
2. In the dropdown, select **your app** (Phantom Inspiration Studio)
3. Click **"Generate Access Token"**
4. Select these permissions:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
   - `instagram_basic`
   - `instagram_content_publish`
5. Click **Generate Access Token** and approve
6. You'll get a **short-lived token** (expires in ~1 hour)

### Part H: Exchange for Long-Lived Token (60 days)

The short-lived token expires quickly. Exchange it for a long-lived token:

1. Go to https://developers.facebook.com/tools/explorer/
2. Make a **GET** request to:
   ```
   GET /oauth/access_token?
     grant_type=fb_exchange_token&
     client_id=YOUR_APP_ID&
     client_secret=YOUR_APP_SECRET&
     fb_exchange_token=YOUR_SHORT_LIVED_TOKEN
   ```
3. Or use this URL in your browser (replace the values):
   ```
   https://graph.facebook.com/v19.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_SHORT_LIVED_TOKEN
   ```
4. The response gives you a **long-lived token** (expires in ~60 days)

### Part I: Get Your Page Access Token (Permanent)

The token from Step H is a **user** token. You need a **Page** token:

1. Go to Graph API Explorer
2. Make a **GET** request to:
   ```
   GET /me/accounts
   ```
3. Find your **PhantomInspiration** Page in the response
4. Copy the **`access_token`** for that Page — this is your **Page Access Token**
5. This token doesn't expire as long as your app stays active

### Part J: Get Your Instagram Business Account ID

1. In Graph API Explorer, make a **GET** request to:
   ```
   GET /me/accounts?fields=instagram_business_account{id,name}
   ```
2. Find the **`instagram_business_account`** object
3. Copy the **`id`** number — this is your **IG Business Account ID**

### Part K: Create the Config Files

Create **two files** (the app supports both Facebook and Instagram):

**File 1:** `config/instagram_credentials.json`
```json
{
  "access_token": "YOUR_PAGE_ACCESS_TOKEN",
  "ig_account_id": "YOUR_IG_BUSINESS_ACCOUNT_ID"
}
```

**File 2:** `config/facebook_credentials.json`
```json
{
  "page_id": "YOUR_PAGE_ID",
  "access_token": "YOUR_PAGE_ACCESS_TOKEN"
}
```

> Both files use the **same Page Access Token** — just different IDs.

### To earn money:
- **Instagram Reels Play Bonus** (invite-only, check your Professional Dashboard)
- **Branded Content** (once you have followers)
- **Subscriptions** (10K+ followers)
- **Facebook In-stream ads**: 10,000 followers + 600,000 minutes watched
- **Facebook Stars**: Virtual gifts during live videos

### ⚠️ Common Mistakes:

| Mistake | Fix |
|---------|-----|
| Created app under Instagram account | Delete it, recreate under Facebook account |
| Instagram is Personal account | Switch to Business/Creator in Instagram app settings |
| Instagram not linked to Facebook Page | Link them in Instagram Settings → Business → Connect Page |
| Token expires after 1 hour | Exchange for long-lived token (Step H), then get Page token (Step I) |
| `instagram_content_publish` not working | App must be in Live mode OR you must be added as admin in Roles |
| Can't see Instagram account in API | Make sure Instagram is linked to the SAME Page the token is for |

---

## 4️⃣ X / Twitter

**Website:** https://developer.x.com

### Steps:
1. Apply for a **Free Developer Account** (describe your use case as "automated video posting")
2. Create a **Project** → Create an **App**
3. Enable **OAuth 2.0** with PKCE
4. Add scopes: `tweet.write`, `users.read`, `tweet.read`
5. Note your **Client ID** and **Client Secret**
6. Create file: `config/x_credentials.json`

### File content:
```json
{
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "redirect_uri": "http://localhost:8080/callback"
}
```

### To earn money:
- **X Ad Revenue Sharing**: Requires **X Premium** ($8/month) + **5M+ tweet impressions/month**
- **Grok Tips**: If you have X Premium

---

## 5️⃣ Rumble (Best for instant monetization)

**Website:** https://rumble.com/account/api

### Steps:
1. Create a **Rumble Account** (free)
2. Go to **Account Settings** → **API**
3. Request **API Access** (usually approved within 24–48 hours)
4. Copy your **API Key**
5. Create file: `config/rumble_credentials.json`

### File content:
```json
{
  "api_key": "YOUR_API_KEY"
}
```

### To earn money:
- **Rumble Revenue Sharing** starts **IMMEDIATELY** — no minimum threshold
- Payout: $0.50–$2.00 per 1,000 views
- **No subscriber minimum** — you earn from day one

---

## 6️⃣ Facebook (Video Uploads to Page)

> **Same app as Instagram!** If you followed Section 3, you already have everything.
> Just add the `pages_manage_posts` permission and create `config/facebook_credentials.json`.

**Website:** https://developers.facebook.com

### Steps (if you already created the app in Section 3):
1. Your app already has the **Facebook Pages API** product
2. Make sure you have `pages_manage_posts` permission
3. Get your **Page ID** from the Graph API Explorer:
   ```
   GET /me/accounts
   ```
4. Find your Page in the response → copy the **`id`** field
5. Create file: `config/facebook_credentials.json`

### File content:
```json
{
  "page_id": "YOUR_PAGE_ID",
  "access_token": "YOUR_PAGE_ACCESS_TOKEN"
}
```

> **Same token as Instagram** — just a different ID. The token from Section 3 Step I works for both.

### To earn money:
- **In-stream ads**: Requires 10,000 followers + 600,000 minutes watched
- **Stars**: Virtual gifts during live videos
- **Reels bonuses**: Invite-only via Professional Dashboard

---

## 7️⃣ Snapchat

**Website:** https://developers.snap.com

### Steps:
1. Create a **Snap Developer Account**
2. Create an app → Enable **"Snap Kit"**
3. For video uploads, you need **Business access** (apply)
4. Create file: `config/snapchat_credentials.json`

### To earn money:
- **Spotlight Rewards**: Payouts for viral videos
- **Snap Ads**: Revenue share

---

## 8️⃣ Pinterest

**Website:** https://developers.pinterest.com

### Steps:
1. Create a **Pinterest Business Account**
2. Go to **Developer Portal** → Create app
3. Get **Access Token**
4. Create file: `config/pinterest_credentials.json`

### To earn money:
- **Idea Pins** can earn through **affiliate links**
- **Product Pins** for e-commerce

---

## 💰 Additional Monetization Sites (No API needed)

These sites pay you for views but don't have upload APIs — you upload manually:

| Site | URL | Payout | Requirements |
|------|-----|--------|-------------|
| **Content Rewards** | https://contentrewards.com | $0.50–$3/1K views | Sign up as creator |
| **Higgsfield Earn** | https://creators.higgsfield.ai | Variable | Connect Instagram |
| **Dailymotion** | https://www.dailymotion.com | Ad revenue share | 1,000 views minimum |
| **Odysee** | https://odysee.com | LBRY credits | None |
| **Vimeo** | https://vimeo.com | Subscription model | Vimeo Pro ($20/mo) |

---

## 📁 Summary: Files You Need to Create

After following this guide, your `config/` folder should look like:

```
config/
  youtube_client_secret.json    ← From Google Cloud Console
  tiktok_credentials.json       ← From TikTok Developers
  instagram_credentials.json    ← From Meta Developers
  x_credentials.json            ← From X Developer Portal
  rumble_credentials.json       ← From Rumble API Settings
```

**Only create files for platforms you actually want to upload to.** The program will skip any platform whose credentials file is missing.

---

## 🚀 Quick Start Checklist

- [ ] Google Cloud Console → Enable YouTube API → Download `youtube_client_secret.json`
- [ ] TikTok Developers → Create app → Save `tiktok_credentials.json`
- [ ] Meta Developers → Create Business app → Save `instagram_credentials.json`
- [ ] X Developer Portal → Create app → Save `x_credentials.json`
- [ ] Rumble → Request API key → Save `rumble_credentials.json`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run the program and start generating/uploading videos!

---

## ❓ FAQ

**Q: Do I need all of these?**
A: No. Start with **YouTube + TikTok + Rumble** — those are the easiest and most profitable.

**Q: Which platform pays the most?**
A: **YouTube** pays the most long-term ($1–$10/1K views). **Rumble** pays fastest (no minimum threshold).

**Q: Can I use the same video on all platforms?**
A: Yes! The program is designed to generate one video and upload it everywhere.

**Q: Do I need a business/company to sign up?**
A: No. All developer accounts are available to individuals.

**Q: How long does API approval take?**
A: YouTube/TikTok/Rumble are instant or within 24 hours. X/Twitter may take 1–3 days.

**Q: I have $0 budget. Can I still use AdSense?**
A: **Yes, absolutely!** AdSense is completely free to sign up for — Google doesn't charge you anything. They take a cut of the ad revenue (not from your pocket). Same for all the platforms listed here — every single API and developer account is **free**. The only exception is X Premium ($8/month) if you want their ad revenue sharing, but that's optional.

**Q: So what's the catch with AdSense?**
A: No catch. Google shows ads on your videos, advertisers pay Google, and Google splits that money with you. You only need to meet the **1,000 subscriber / 4,000 hour** threshold first. Until then, your videos still get uploaded and visible — you just don't earn yet.

**Q: Which platforms can I earn on with $0 budget?**
A: All of them except X/Twitter's ad program (which needs Premium). **Rumble** is the best starting point because they pay from day one with no minimums.
