# Changelog - Isocrates Bot

## [Unreleased] - 2025-11-14

### Removed - Simplified Bot by Removing Unused Features

#### 1. Removed Referral System

- **Before**: Users had unique referral codes and could track who they invited
- **After**: Referral system completely removed - users just register directly
- Removed `/myreferral` command
- Removed referral code handling from `/start` command
- Database fields kept for backward compatibility but marked as deprecated
- Functions `find_user_by_referral_code()` and `get_user_referral_info()` marked as deprecated

#### 2. Removed MyTicket Command

- **Before**: Users could use `/myticket` to view their ticket status
- **After**: `/myticket` command removed - ticket codes are provided immediately upon approval
- Users receive ticket code via direct message when admin approves registration
- For free events, ticket code is provided immediately upon registration

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
  - Removed `my_ticket()` function
  - Removed `my_referral()` function
  - Updated `start()` function to remove referral code handling
  - Updated `start()` function to automatically register users
  - Added logic to check for active discount codes before prompting
  - Removed `handle_choice()` function (no longer needed)
  - Updated `help_command()` to remove references to `/myticket` and `/myreferral`
  - Free events now register immediately after showing event details
  - Paid events check for discount availability before asking

- `bot/core.py`:
  - Removed `CommandHandler` for `/myreferral`
  - Removed `CommandHandler` for `/myticket`
  - Updated `user_conv_handler` to remove `CHOOSING` state
  - Simplified conversation flow

- `database.py`:
  - Added deprecation notices to referral-related functions
  - Marked `find_user_by_referral_code()` as DEPRECATED
  - Marked `get_user_referral_info()` as DEPRECATED
  - Added schema comments noting deprecated fields in users table
  - Database fields maintained for backward compatibility

- `config.py`:
  - Removed `CHOOSING` from user conversation states
  - Updated state numbering: User states now `range(3)` instead of `range(4)`
  - Updated admin state numbering to `range(3, 19)` instead of `range(4, 20)`

### User Experience Improvements

**New Flow for Free Events:**

``` text
/start → Show event details → Immediate registration → Get ticket code
```

**New Flow for Paid Events (with discount codes):**

``` text
/start → Show event details → "Do you have a discount code?" →
Enter code or skip → Payment instructions → Upload receipt
```

**New Flow for Paid Events (no discount codes):**

``` text
/start → Show event details → Payment instructions → Upload receipt
```

This creates a much smoother, more intuitive registration experience!
