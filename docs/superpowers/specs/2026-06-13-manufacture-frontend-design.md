# Manufacture Frontend Design

Date: 2026-06-13

## Goal

Build a standalone frontend for Los Andalus manufacturing at `/los-andalus/manufacture`.
The first release starts with a custom login page, a small manufacture home screen, and the Food Logger flow represented by the existing HTML references in `docs/Manufacture`.

## Approved Direction

Use Vue 3, Vite, Frappe UI, Tailwind, and Frappe-backed APIs.

This is the preferred stack because Frappe UI is built for Vue 3 and Tailwind, current Frappe frontend examples use this family of tools, and the existing Food Logger HTML already follows a Tailwind-style visual system with Arabic-first content.

## Route Structure

The standalone app is mounted at:

`/los-andalus/manufacture`

Client routes:

- `/login`: custom login page.
- `/home`: manufacture home screen after login.
- `/food-logger/new`: Food Logger data entry.
- `/food-logger/summary`: review and confirmation.
- `/food-logger/success`: saved batch success state.

The route spelling is `manufacture`.

## Authentication

The app uses a custom Vue login page, but authentication is handled by Frappe.

Successful login creates the normal Frappe session cookie. The frontend does not store passwords, create a separate user table, or implement a parallel auth system. Route guards check the current Frappe session before allowing access to `/home` or Food Logger routes.

Expected behavior:

- Anonymous users opening `/los-andalus/manufacture` see the custom login page.
- Authenticated users opening `/los-andalus/manufacture` are routed to `/home`.
- Expired sessions return the user to `/login`.
- API calls use the active Frappe user, roles, and permissions.

## Localization

The app supports Arabic and English from the start.

All visible strings go through a `t()` localization helper. Translations are managed through Frappe's translation system, including the Translation DocType/localization workflow, instead of hardcoded component-level bilingual maps.

Layout supports both directions:

- Arabic: RTL, Arabic-first visual default.
- English: LTR.

Direction changes must affect layout alignment, navigation, form controls, icons where direction matters, and text flow.

## First Release Scope

The first release includes:

- Custom login screen.
- Manufacture home screen.
- Food Logger data-entry screen.
- Food Logger summary and confirmation screen.
- Food Logger success screen.
- Session route guards.
- Localization foundation with `t()`.
- Frappe API integration layer.

The first release does not include a wide manufacturing dashboard, analytics, production planning, inventory dashboards, or multi-module navigation beyond what is needed to reach Food Logger cleanly.

## Food Logger Reference Screens

Existing local references:

- `docs/Manufacture/Food Logger - Data Entry - تسج (1).html`
- `docs/Manufacture/Food Logger - Summary & Confir.html`
- `docs/Manufacture/Food Logger - Success Overlay.html`

These files are references for workflow, fields, visible content, and visual direction. The implementation should rebuild the UI as Vue components rather than embedding these static HTML files.

## Main Screens

### Login

The login page should feel like part of the Los Andalus manufacturing product, not the default Frappe Desk login. It should include username/email, password, submit, loading, error, and expired-session states.

The page calls Frappe auth and relies on Frappe session cookies after success.

### Manufacture Home

The home screen is a small authenticated landing page for manufacturing workflows.

Initial content:

- Product/manufacturing identity.
- Current user/session context.
- Primary entry point to Food Logger.
- Clear logout action.
- Room for future manufacturing modules without building them in the first release.

### Food Logger Data Entry

The data-entry screen follows the existing HTML reference:

- Batch context.
- Product selection.
- Raw materials table/list.
- Planned and actual quantities.
- Production output quantities.
- Waste and loss sections.
- Notes.
- Continue/calculate action.

### Food Logger Summary

The summary screen follows the existing HTML reference:

- Selected product and batch summary.
- Produced quantity.
- Unit cost and total cost.
- Waste percentage.
- Raw material breakdown.
- Waste breakdown.
- Loss breakdown.
- Notes.
- Confirmation checkbox.
- Save action.

### Food Logger Success

The success screen follows the existing HTML reference:

- Saved-state confirmation.
- Batch reference.
- Product and quantity summary.
- Total cost and unit cost.
- Save details.
- Copy batch reference.
- Quick actions.
- Start new batch.

## Data And API Plan

The frontend should use a small API layer rather than calling Frappe APIs directly from every component.

Initial API responsibilities:

- Get current session user.
- Login.
- Logout.
- Load products available for Food Logger.
- Load raw material defaults for selected product.
- Calculate or preview production costs.
- Save production batch.
- Fetch saved batch confirmation data.

Backend implementation can use Frappe document APIs where suitable and whitelisted methods where business logic or validation is needed.

Likely domain concepts:

- Production batch.
- Product.
- Raw material line.
- Production output line.
- Waste line.
- Loss line.
- Batch confirmation.

Exact DocType names and fields should be finalized during implementation planning.

## Component Boundaries

Suggested frontend modules:

- App shell and route guards.
- Authentication views and session store.
- Localization helper and direction handling.
- Manufacture home.
- Food Logger feature module.
- Shared UI primitives for buttons, inputs, cards/panels, tables, numeric controls, empty/error/loading states.
- API client/resources.

Food Logger should be split into focused components for product selection, materials, output, waste/loss, notes, summary sections, and success details.

## Error Handling

The UI should handle:

- Invalid login credentials.
- Expired sessions.
- Permission-denied API responses.
- Network/server errors.
- Validation errors before saving a batch.
- Failed save attempts.
- Missing product/material configuration.

Errors should be localized with `t()` and should preserve user-entered data when possible.

## Testing And Verification

Implementation should verify:

- Vue app builds successfully.
- Standalone route loads at `/los-andalus/manufacture`.
- Anonymous users see login.
- Successful Frappe login reaches manufacture home.
- Route guards protect authenticated screens.
- Arabic and English text use `t()`.
- RTL and LTR layouts render correctly.
- Food Logger data can move from entry to summary to success.
- Save behavior uses Frappe backend APIs.
- Mobile and desktop layouts are usable.

Browser verification should cover the login, home, Food Logger entry, summary, and success states.

## Open Implementation Decisions

- Final DocType names and field schema.
- Whether cost calculation is frontend-preview-only, backend-authoritative, or both.
- Exact permission roles for manufacturing users.
- Whether the app should support offline draft entry in a later release.
