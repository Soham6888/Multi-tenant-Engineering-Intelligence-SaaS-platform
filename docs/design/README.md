# Design preview

The interface uses a forest-green sidebar, warm-neutral canvas, restrained emerald and sage charts, and self-hosted DM Sans/Manrope typography. The responsive shell uses compact tables on desktop, contained horizontal scrolling on mobile, and keyboard-accessible navigation/dialogs.

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
