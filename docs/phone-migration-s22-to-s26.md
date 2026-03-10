# Samsung S22 Ultra -> S26 Ultra Migration Checklist

**Goal:** Clean migration -- treat this as a fresh start, not a clone of the old phone.

---

## Phase 0: Pre-Migration Prep (Do All of This BEFORE Touching the S26)

### Back Up Authenticators (CRITICAL -- Do This First)

- [ ] **Google Authenticator**
  - Open Google Authenticator on S22
  - Confirm cloud sync is ON: tap profile icon > check "Synced to [your Google account]"
  - If not synced: sign in to your Google account within the app to enable sync
  - Alternative: Menu (three dots) > Transfer accounts > Export accounts > generates QR code
  - DO NOT delete the app from S22 until S26 is fully verified

- [ ] **Microsoft Authenticator**
  - Open Microsoft Authenticator on S22
  - Go to Settings (three dots top-right) > Cloud Backup > toggle ON
  - Confirm it says "Backed up to [your Microsoft account]"
  - Write down which accounts use MS Authenticator (you may need to re-verify some)
  - DO NOT delete the app from S22 until S26 is fully verified

### Back Up Privacy Documents

- [ ] Identify all privacy documents on S22 (check Downloads, Documents, My Files)
- [ ] Copy privacy documents to one of these:
  - Google Drive (encrypted folder recommended)
  - OneDrive
  - USB-C flash drive (plug directly into S22, copy files)
  - Samsung Smart Switch PC backup
- [ ] Verify copies are accessible from a computer or cloud before proceeding

### General Backup

- [ ] Samsung Cloud backup: Settings > Accounts > Samsung account > Samsung Cloud > Back up data
- [ ] Google backup: Settings > Accounts > Google > Back up to Google Drive
- [ ] Photos: Confirm Google Photos backup is complete (open app, check sync status)
- [ ] WhatsApp / Signal / Telegram: Back up chats within each app
- [ ] Notes: Samsung Notes syncs via Samsung Cloud -- confirm sync is current
- [ ] Contacts: Should be synced to Google account -- verify at contacts.google.com

---

## Phase 1: Audit Your S22 (The Cleanup Opportunity)

Before migrating, go through your S22 and decide what to keep. Open Settings > Apps and review.

### Apps to KEEP (install fresh on S26)

Go through each category and check what you actually use:

- [ ] Review and mark keepers below

### Apps to DROP (don't bring over)

- [ ] Delete or note apps you haven't opened in 3+ months
- [ ] Remove old games you don't play
- [ ] Remove duplicate utility apps (e.g., 3 flashlight apps)
- [ ] Remove apps that were only needed for old phone (S22-specific tools)

### Data Cleanup

- [ ] Delete old screenshots you don't need
- [ ] Clear Downloads folder of junk
- [ ] Remove old APKs
- [ ] Archive or delete old voice recordings
- [ ] Clean up photo gallery (delete blurry photos, duplicates)

---

## Phase 2: S26 Ultra Initial Setup

- [ ] Charge S26 to 100% before starting
- [ ] Power on and go through language/Wi-Fi setup
- [ ] **Skip Smart Switch** -- do a clean setup instead (recommended when jumping 4 generations)
  - Smart Switch across multiple generations often causes notification bugs, battery drain, and data corruption
  - Fresh install = clean start = better performance
- [ ] Sign in to Google account
- [ ] Sign in to Samsung account
- [ ] Set up fingerprint + face unlock
- [ ] Set up screen lock (PIN/pattern)
- [ ] Transfer eSIM or insert physical SIM

---

## Phase 3: Restore Authenticators

- [ ] **Google Authenticator**
  - Install from Play Store
  - Sign in with same Google account
  - Codes should sync automatically
  - Verify by checking a few 2FA codes match between old and new phone
  - If codes didn't sync: use QR code transfer method from S22

- [ ] **Microsoft Authenticator**
  - Install from Play Store
  - DO NOT set up any accounts manually yet
  - Tap "Begin Recovery" on first launch
  - Sign in with same Microsoft account used for backup
  - Accounts restore automatically
  - Some accounts may require re-verification (sign in again)
  - Verify codes work before wiping S22

---

## Phase 4: Install Apps (Clean List)

Only install what you actually use. Below is a curated checklist organized by category.

### Google Apps (Install from Play Store)

Core (likely preinstalled on S26):
- [ ] Gmail
- [ ] Google Maps
- [ ] Google Chrome
- [ ] Google Photos
- [ ] YouTube
- [ ] Google Drive
- [ ] Google Calendar
- [ ] Google Messages (RCS)
- [ ] Google Phone (dialer)
- [ ] Google Contacts
- [ ] Google Clock
- [ ] Google Calculator
- [ ] Google Keep (notes)
- [ ] Google Files
- [ ] Google Play Store

Install if you use them:
- [ ] Google Docs
- [ ] Google Sheets
- [ ] Google Slides
- [ ] Google Meet
- [ ] Google Chat
- [ ] Google Wallet (tap to pay)
- [ ] Google Home (smart home devices)
- [ ] Google Fit / Pixel Watch (fitness tracking)
- [ ] Google Podcasts (or YouTube Music for podcasts)
- [ ] YouTube Music
- [ ] Google Translate
- [ ] Google Lens (may be built into Camera)
- [ ] Google Earth
- [ ] Google News
- [ ] Google One (storage management)
- [ ] Google Gemini (AI assistant)
- [ ] Google Recorder
- [ ] Google Authenticator

### Microsoft Apps

- [ ] Microsoft Authenticator
- [ ] Outlook (if used for work/personal email)
- [ ] Microsoft 365 (Word/Excel/PowerPoint combined)
- [ ] OneDrive
- [ ] Microsoft Teams (if used for work)
- [ ] Microsoft Edge (if preferred browser)
- [ ] LinkedIn (if used)

### Samsung Apps (Preinstalled -- Keep or Disable)

Likely preinstalled, decide which to keep:
- [ ] Samsung Internet (keep or disable in favor of Chrome)
- [ ] Samsung Notes
- [ ] Samsung Health
- [ ] Samsung Members
- [ ] Galaxy Wearable (if you have a Galaxy Watch)
- [ ] Samsung Gallery
- [ ] Samsung My Files
- [ ] Samsung SmartThings (smart home)
- [ ] Samsung Global Goals (disable if not used)
- [ ] Samsung Free / Samsung News (disable if not used)
- [ ] Bixby (disable if not used)

### Communication

- [ ] Phone (default)
- [ ] Messages (default)
- [ ] WhatsApp
- [ ] Signal
- [ ] Telegram
- [ ] Discord
- [ ] Slack (if used for work)

### Social Media (only install what you actively use)

- [ ] Twitter/X
- [ ] Instagram
- [ ] Reddit
- [ ] Facebook (or skip -- use browser version to save battery)
- [ ] TikTok
- [ ] Threads

### Finance / Banking

- [ ] Your bank app(s)
- [ ] Credit card app(s)
- [ ] Venmo / Zelle / Cash App
- [ ] Robinhood / brokerage app
- [ ] Google Wallet

### Productivity

- [ ] Obsidian (for your briefing notes)
- [ ] Todoist / TickTick / task manager
- [ ] Calendar widget app (if using one beyond Google Calendar)
- [ ] Password manager (Bitwarden / 1Password / LastPass)

### Utilities

- [ ] VPN app (if used)
- [ ] Ad blocker (Samsung Internet supports extensions, or use DNS-based like NextDNS)
- [ ] QR code scanner (built into Samsung Camera)
- [ ] File manager (Samsung My Files or Google Files)

### Media / Entertainment

- [ ] Spotify / Apple Music / YouTube Music
- [ ] Netflix / Hulu / Disney+ / streaming apps
- [ ] Kindle / reading app
- [ ] Pocket Casts / podcast app

### Health / Fitness

- [ ] Samsung Health
- [ ] MyFitnessPal / fitness tracker
- [ ] Sleep tracker

---

## Phase 5: Transfer Privacy Documents

- [ ] Download privacy documents from cloud storage (Drive/OneDrive) to S26
- [ ] Or connect USB-C flash drive to S26 and copy over
- [ ] Organize into a dedicated folder: My Files > Documents > Privacy
- [ ] Verify all documents open correctly

---

## Phase 6: Configure S26 Settings

- [ ] Notifications: Review per-app notification settings
- [ ] Battery: Turn on Adaptive Battery
- [ ] Display: Set refresh rate (Adaptive 1-120Hz recommended)
- [ ] Always-On Display: Configure to your preference
- [ ] S Pen: Configure Air Actions and shortcuts
- [ ] Default apps: Set preferred browser, email, messages, phone
- [ ] Dark mode: Toggle on if preferred
- [ ] Digital Wellbeing: Set app timers if desired
- [ ] Do Not Disturb: Configure schedule

---

## Phase 7: Final Verification

- [ ] Make a test phone call
- [ ] Send and receive a test text (SMS and RCS)
- [ ] Verify Google Authenticator codes work on a real login
- [ ] Verify Microsoft Authenticator codes work on a real login
- [ ] Verify all privacy documents are accessible
- [ ] Verify photos are accessible (Google Photos or local)
- [ ] Check all banking/financial apps work (may need re-verification)
- [ ] Verify Google Wallet tap-to-pay works (if used)
- [ ] Confirm email accounts are receiving mail

---

## Phase 8: Decommission S22 Ultra

**Wait at least 1 week before wiping the S22** -- you'll want it as a fallback.

- [ ] Confirm everything works on S26 for 7 days
- [ ] Remove Google account from S22
- [ ] Remove Samsung account from S22
- [ ] Factory reset S22: Settings > General Management > Reset > Factory Data Reset
- [ ] Decide: keep as backup, sell, trade in, or recycle
