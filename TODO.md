## Development

- [x] Basic port of `hugo-ink`.
- [x] Migrate all blog posts and convert them to `toml` frontmatter.
- [x] Syntax highlight fixes
- [x] Fix images.
- [x] Title bar - Blog title
- [x] Verify all SEO/meta tags are present.
- [x] Add macro for meta tags
- [x] Add support for `image` parameter in individual blog posts. They'll be used for `og:image` in `blog_page` header.
- [x] Add RSS Feed support.
- [x] Add search bar.
- [ ] Add `draft` support.
- [ ] Updated/Article Published meta tags.

## Content

- [ ] Rewrite home page.
- [x] Contact `/contact` page.
- [x] Add a causes page.
- [x] Redo the `setup` page.
- [ ] Add a `/now` page.
- [ ] _Consider_ adding a `/til` page.

## Design

- [x] `pygments` or similar code-highlighting support.

## Deployment

- [ ] Setup `mrkaran.dev` CNAME to DO Droplet with Cloudflare.
- [ ] Setup Github Actions/DroneCI to `rsync` the assets to Droplet.
- [ ] Deploy `shynet` for analytics.

## Post Release

- [ ] Write a blog post on why the migration from `Hugo` to `Zola`.

## Future

- [ ] Port `hugo-ink` + customisations made on this site as a `zola` theme.
