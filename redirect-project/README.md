# The old subdomain's redirect

`chronoscape.charlietrenorden.com` is a Cloudflare Pages project called
`chronoscape-timeline`. It served the site until the move to GitHub Pages on
20/08/2026, and then kept serving a **frozen copy of the whole thing** for a week:
200, not a redirect, indexed by Google and Bing and still reporting pageviews to the
stats dashboard. Everyone, including a comment in the hub's `index.html` and the
estate head check, believed it was already redirecting.

This directory is what it serves now. To redeploy it:

    npx wrangler pages deploy redirect-project --project-name chronoscape-timeline

Deleting the project instead would have been simpler and wrong: three of its recorded
referrals are search engines and 48 are direct, so deletion 404s anyone arriving from
a bookmark or a search result. `:splat` carries the rest of the path, so `/iceland/`
lands on `/chronoscape/iceland/` rather than on the front page.

Do NOT deploy the built site here again. See the header of `.github/workflows/deploy.yml`.
