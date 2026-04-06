#!/bin/bash

# Check if URL is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <URL> [screenshot|dump]"
    exit 1
fi

URL="$1"
MODE="${2:-dump}" # Defaults to screenshot if not specified

# 2. Extract checkin and checkout timestamps (ms)
CHECKIN_MS=$(echo "$URL" | grep -oP 'checkin=\K[0-9]+')
CHECKOUT_MS=$(echo "$URL" | grep -oP 'checkout=\K[0-9]+')

# 3. Convert Milliseconds to Seconds
IN_SEC=$((CHECKIN_MS / 1000))
OUT_SEC=$((CHECKOUT_MS / 1000))

# 4. Create readable dates
READABLE_IN=$(date -d "@$IN_SEC" +%Y-%m-%d 2>/dev/null || date -r "$IN_SEC" +%Y-%m-%d)
READABLE_OUT=$(date -d "@$OUT_SEC" +%Y-%m-%d 2>/dev/null || date -r "$OUT_SEC" +%Y-%m-%d)

# 5. Handle the output format based on Mode
if [ "$MODE" == "dump" ]; then
    FILENAME="booking_${READABLE_IN}_to_${READABLE_OUT}.html"
    COMMAND="shot-scraper html"
else
    FILENAME="booking_${READABLE_IN}_to_${READABLE_OUT}.png"
    COMMAND="shot-scraper"
fi

echo "--------------------------------------------------------------------"
echo "Mode: $MODE | Saving to: $FILENAME"
echo "--------------------------------------------------------------------"

export PYTHONUTF8=1 # FIX GITBASH UnicodeEncodeError: 'charmap' codec can't encode character '\u010c' in position

# 6. Run shot-scraper
uvx $COMMAND "$URL" \
  --output "$FILENAME" \
  --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  --wait 10000 \
  --javascript "
    new Promise(async (resolve) => {
      // 1. Handle Cookies
      const cookieBtn = document.querySelector('#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll');
      if (cookieBtn) {
        cookieBtn.click();
        await new Promise(r => setTimeout(r, 1000));
      }

      // 2. Expand 'Info' sections
      const infoButtons = Array.from(document.querySelectorAll('button, a'))
                               .filter(el => el.innerText && el.innerText.includes('INFO AND BOOK'));
      infoButtons.forEach(btn => btn.click());

      // Wait for animations to finish
      setTimeout(resolve, 3000);
    });
  "
