# Manual / exploratory test cases

Manual test documentation that complements the automation: some checks are cheaper and more reliable done by a person.

## TC-001 - Empty search (mobile)

**Precondition:** app open on the Home screen
**Steps:**
1. Tap "Search Wikipedia"
2. Leave the field empty and tap back
**Expected result:** the app returns to Home without a crash, and the next search does not start in a stuck state.
**Type:** functional / edge case

## TC-002 - Rotate during a search (mobile)

**Precondition:** a search in progress with results on screen
**Steps:**
1. Rotate the device to landscape
2. Rotate back to portrait
**Expected result:** the search results stay on screen, with no lost state.
**Type:** exploratory

## TC-003 - Dropdown with the keyboard (web)

**Precondition:** the `/dropdown` page is loaded
**Steps:**
1. Focus the dropdown with Tab (keyboard, not mouse)
2. Select an option with the arrow keys and Enter
**Expected result:** the right option is selected, same as with the mouse.
**Type:** accessibility / regression

## Prioritization

In a suite that runs every week before a release, TC-001 is a good candidate for automation: repetitive, little judgment needed. TC-002 and TC-003 are worth more as a periodic manual checklist, because they depend on gesture and accessibility behavior that is more expensive to automate reliably than to check by hand now and then.
