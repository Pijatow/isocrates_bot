# Admin Notifications Update

## Changes Made

### Previous Behavior
- Receipt notifications were sent to a single `ADMIN_CHAT_ID` (could be a group or channel)
- Only one location received notifications about new registrations

### New Behavior
- Receipt notifications are now sent to ALL admin users individually
- Each admin user ID in `ADMIN_USER_IDS` receives:
  1. A photo of the payment receipt with details
  2. A text notification for high visibility

### Benefits
- ✅ All admins are notified directly in their private chats
- ✅ Admins can approve/reject from their personal Telegram
- ✅ No need for a separate admin group/channel
- ✅ More flexible admin management
- ✅ Error handling: if sending to one admin fails, others still get notified

### Technical Details

**Modified Files:**
- `bot/handlers.py`:
  - `handle_receipt()` function now loops through `ADMIN_USER_IDS`
  - Sends receipt photo and notification to each admin individually
  - Added error handling for failed notifications

- `bot/admin.py`:
  - Beautified approval message with emojis and better formatting
  - Beautified rejection message with clearer explanation

- `config.py`:
  - `ADMIN_CHAT_ID` marked as deprecated (kept for backward compatibility)
  - Validation now only requires `ADMIN_USER_IDS` (not `ADMIN_CHAT_ID`)

### Configuration

**Required in .env:**
```
ADMIN_USER_IDS=123456789,987654321,555555555
```

**Optional (deprecated):**
```
ADMIN_CHAT_ID=...  # No longer used
```

### Error Handling
If sending a notification to one admin fails, the error is logged and the bot continues sending to the remaining admins. This ensures maximum delivery reliability.

### Message Format

**Receipt Photo Caption:**
```
📸 New Payment Receipt

Event: '[Event Name]'
From: User [ID:xxx, UNAME:xxx, NAME:'xxx']
Fee Paid: 150,000 Toman
Discount Used: SUMMER25
```

**Text Notification:**
```
📢 New receipt from [Name] (@username) requires verification.
```

**Approval Message to User:**
```
🎉 Registration Approved!

Congratulations! Your payment has been verified and your registration is confirmed!

🎫 Your ticket code:
ABC12345

See you at the event! 🎊
```

**Rejection Message to User:**
```
❌ Registration Not Approved

Unfortunately, your registration could not be approved at this time.

If you have questions or believe this was a mistake, please contact an admin.
```

## Migration Notes

If you previously used `ADMIN_CHAT_ID` pointing to a group/channel:
1. Simply ensure all admin user IDs are listed in `ADMIN_USER_IDS`
2. You can remove `ADMIN_CHAT_ID` from your `.env` file (optional)
3. No database changes required

The bot will now send notifications directly to each admin's private chat instead of to the group/channel.
