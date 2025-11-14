# Changelog - Isocrates Bot

## [Unreleased] - 2025-11-14

### Changed - User Registration Flow Improvements

#### 1. Removed Unnecessary Confirmation Step
- **Before**: Users had to click `/start`, then choose "Yes, Register Me!" or "No, thanks."
- **After**: Users who click `/start` are immediately registered (they clearly want to register if they clicked the button)
- Removed the `CHOOSING` conversation state
- Removed the `handle_choice()` function
- Updated conversation handler to remove the confirmation step

#### 2. Smart Discount Code Prompting
- **Before**: Bot always asked "Do you have a discount code?" for every paid event
- **After**: Bot only asks about discount codes if there are active codes available for the event
- Checks for active discount codes with `uses_left > 0` before prompting
- If no discount codes exist, users go directly to payment instructions
- Improved user experience by not asking unnecessary questions

### Technical Changes

**Modified Files:**
- `bot/handlers.py`:
  - Updated `start()` function to automatically register users
  - Added logic to check for active discount codes before prompting
  - Removed `handle_choice()` function (no longer needed)
  - Free events now register immediately after showing event details
  - Paid events check for discount availability before asking

- `bot/core.py`:
  - Updated `user_conv_handler` to remove `CHOOSING` state
  - Simplified conversation flow

- `config.py`:
  - Removed `CHOOSING` from user conversation states
  - Updated state numbering: User states now `range(3)` instead of `range(4)`
  - Updated admin state numbering to `range(3, 19)` instead of `range(4, 20)`

### User Experience Improvements

**New Flow for Free Events:**
```
/start → Show event details → Immediate registration → Get ticket code
```

**New Flow for Paid Events (with discount codes):**
```
/start → Show event details → "Do you have a discount code?" →
Enter code or skip → Payment instructions → Upload receipt
```

**New Flow for Paid Events (no discount codes):**
```
/start → Show event details → Payment instructions → Upload receipt
```

This creates a much smoother, more intuitive registration experience!
