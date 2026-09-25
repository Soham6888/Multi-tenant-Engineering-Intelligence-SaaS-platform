# Design preview

The updated workspace uses a dark slate sidebar, cool neutral canvas, mint accents, self-hosted DM Sans/Manrope typography and larger headings. A delivery focus panel brings the sample review queue above the aggregate charts. Queue items drill into the matching repository and PR state; the queue snapshot is explicitly independent of the chart date range. Rounded panels and restrained shadows separate information without hiding data density.

The responsive shell retains contained horizontal table scrolling and keyboard-accessible navigation/dialogs. The focus panel stacks on narrower screens, with readable queue details and touch targets. The visual refresh is authorized by the user's request for a more modern UI; it does not imply GitHub is connected.

- [Desktop dashboard](overview-desktop.png)
- [Mobile dashboard](overview-mobile.png)
- [Desktop sign-in](login-desktop.png)
- [Mobile create-account](register-mobile.png)

The screenshots come from the running Next.js app:

```powershell
cd frontend
npm run screenshots
```

The login, registration and account pages use FastAPI through the Next.js auth proxy. They do not sign in to the independent demo workspace. Dashboard values remain explicitly identified as sample data.
